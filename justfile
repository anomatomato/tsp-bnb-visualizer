alias s := setup
alias t := test
alias u := update-all

pre_commit_file := ".pre-commit-config.yaml"
pre_commit_msg := "chore(deps): update pre-commit hooks"
uv_lock_file := "uv.lock"
requirements_file := "requirements.txt"
python_update_commit_msg := "chore(deps): update python packages"

# Install python dependencies
install:
    uv sync --all-packages --all-extras --all-groups

# Install pre-commit hooks
pre_commit_setup:
    uv run pre-commit install

# Install python dependencies and pre-commit hooks
setup: install pre_commit_setup

# Run pytest
test:
    uv run pytest src

# Update everything relevant
update-all: update-pre-commit update-python

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
