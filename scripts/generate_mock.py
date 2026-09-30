"""Generate a fresh eil51 run and copy it into the frontend mock directory."""

import shutil
from pathlib import Path

from examples.run_tsplib import run_eil51

MOCK_DIR = Path("frontend") / "src" / "mock" / "eil51"


def main() -> None:
    run_dir = run_eil51(open_browser=False)

    if MOCK_DIR.exists():
        shutil.rmtree(MOCK_DIR)  # wipe: stale SVGs from older runs
    MOCK_DIR.mkdir(parents=True)
    shutil.copy2(run_dir / "bnb_state.json", MOCK_DIR / "bnb_state.json")
    shutil.copytree(run_dir / "images", MOCK_DIR / "images")
    print(f"Mock updated: {run_dir} -> {MOCK_DIR}")


if __name__ == "__main__":
    main()
