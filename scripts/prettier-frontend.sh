#!/usr/bin/env bash
# Format frontend files with frontend's OWN prettier (resolves
# prettier-plugin-tailwindcss from frontend/node_modules).
#
# pre-commit passes repo-root-relative paths ("frontend/src/App.tsx");
# prettier's plugin resolution is anchored at the working directory, so we
# must run from inside frontend/ with the prefix stripped.
set -euo pipefail

cd "$(dirname "$0")/../frontend"

args=()
for f in "$@"; do
  args+=("${f#frontend/}")
done

exec pnpm exec prettier --write -- "${args[@]}"
