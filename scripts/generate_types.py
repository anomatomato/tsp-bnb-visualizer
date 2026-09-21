"""Regenerate frontend/src/types/bnb.ts from tsp_bnb/export/models.py.

Run: uv run python -m scripts.generate_types   (from repo root)
Output is committed; hand edits will be overwritten.
"""

from pydantic2ts import generate_typescript_defs


def main() -> None:
    generate_typescript_defs(
        "tsp_bnb.export.models",  # dots, not slashes
        "frontend/src/types/api-types.ts",
    )


if __name__ == "__main__":
    main()
