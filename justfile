alias s := setup
alias e := example
alias c := clean
alias t := test
alias u := update-all
alias uf := update-frontend

pre_commit_file := ".pre-commit-config.yaml"
pre_commit_msg := "chore(deps): update pre-commit hooks"
uv_lock_file := "uv.lock"
requirements_file := "requirements.txt"
python_update_commit_msg := "chore(deps): update python packages"
frontend_dir := "frontend"
frontend_update_commit_msg := "chore(deps): update frontend packages"

# frontend tool binaries (json2ts, …) for recipes that shell out to Node
export PATH := "frontend/node_modules/.bin:" + env("PATH")

# Install python dependencies
install:
    uv sync --all-packages --all-extras --all-groups

# Install pre-commit hooks
pre_commit_setup:
    lefthook install

# Install frontend dependencies
frontend_install:
    pnpm -C {{ frontend_dir }} install

# Install python + frontend dependencies and pre-commit hooks
setup: install pre_commit_setup frontend_install

# Run pytest
test:
    uv run pytest

# Regenerate frontend types from Pydantic export models
types:
    uv run python -m scripts.generate_types

# Cleanup run artifacts (regenerates an empty catalog so open tabs see
# "no runs" instead of a 404 error boundary)
clean:
    rm -rf output/runs/*
    uv run python -c "from tsp_bnb.export.viewer import write_run_index; write_run_index()"

# Update everything relevant
update-all: update-pre-commit update-python update-frontend

# Update pre-commit hooks
update-pre-commit:
    #!/usr/bin/env bash
    set -euxo pipefail
    uv run pre-commit autoupdate
    if ! git diff --quiet -- {{ pre_commit_file }}; then
        echo "Changes detected in {{ pre_commit_file }}, committing..."
        git add {{ pre_commit_file }}
        git commit -m "{{ pre_commit_msg }}"
    else
        echo "pre-commit hooks already up to date."
    fi

# Update python dependencies
update-python:
    #!/usr/bin/env bash
    set -euxo pipefail
    uv python upgrade
    uv sync --upgrade --all-packages --all-extras --all-groups
    if ! git diff --quiet -- {{ uv_lock_file }}; then
        echo "Changes detected in {{ uv_lock_file }}, exporting requirements and committing..."
        uv export --frozen --output-file={{ requirements_file }}
        git add {{ uv_lock_file }} {{ requirements_file }}
        git commit -m "{{ python_update_commit_msg }}"
    fi

# Update frontend dependencies to latest versions (majors allowed; rewrites package.json + lockfile)
update-frontend *FLAGS:
    #!/usr/bin/env bash
    set -euxo pipefail
    mise exec -- pnpm -C {{ frontend_dir }} update {{FLAGS}}
    if ! git diff --quiet -- {{ frontend_dir }}/pnpm-lock.yaml {{ frontend_dir }}/package.json; then
        echo "Changes detected in frontend lockfile/manifest, committing..."
        git add {{ frontend_dir }}/pnpm-lock.yaml {{ frontend_dir }}/package.json
        git commit -m "{{ frontend_update_commit_msg }}"
    else
        echo "frontend packages already up to date."
    fi

# Run tsplib example script
example:
    uv run python -m examples.run_tsplib

# Build frontend and publish the viewer beside the run archive
publish:
  pnpm -C {{ frontend_dir }} build
  rm -f output/index.html
  rm -rf output/assets
  cp -r frontend/dist/index.html frontend/dist/assets output/

# Serve viewer + all runs (manual convenience; solver auto-starts one too).
# Ensure/reuse the detached server, refresh the catalog, print the URL.
# Watch live logs: tail -f output/.server.log
# Raw foreground alternative: uv run python -m http.server --directory output 8123
serve:
    uv run python -m tsp_bnb.export.viewer

# Stop the detached viewer server (idempotent)
serve-stop:
    uv run python -m tsp_bnb.export.viewer stop
