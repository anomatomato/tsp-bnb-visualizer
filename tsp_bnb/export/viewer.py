"""Viewer serving: detached localhost server + run catalog for the built frontend.

The exported run archive (`output/runs/`) and the published viewer
(`output/index.html` + `output/assets/`) are served together by a detached
stdlib `http.server` bound to localhost. `ensure_viewer()` starts or reuses
that server; `stop_server()` stops the one we spawned; `write_run_index()`
regenerates `runs/index.json` — the catalog the viewer's run picker loads.

Must run from the repository root: OUTPUT_ROOT is CWD-relative.
"""

import errno
import json
import logging
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import psutil
from pydantic import ValidationError

from .models import BnBRunData

logger = logging.getLogger(__name__)

OUTPUT_ROOT = Path("output")
DEFAULT_HOST = "127.0.0.1"  # localhost only
DEFAULT_PORT = 8123
PID_FILE = OUTPUT_ROOT / ".server.pid"
SERVER_LOG = OUTPUT_ROOT / ".server.log"
SPAWN_TIMEOUT_S = 2.0
STOP_TIMEOUT_S = 2.0


def resolve_port() -> int:
    return int(os.environ.get("BNB_VIEWER_PORT", DEFAULT_PORT))


def port_is_free(port: int, host: str = DEFAULT_HOST) -> bool:
    """True if nothing is listening: we can bind the port ourselves."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
        except OSError as e:
            # POSIX sets errno.EADDRINUSE; Windows winsock errors carry
            # winerror 10048 (WSAEADDRINUSE) with errno=None instead.
            if e.errno == errno.EADDRINUSE or getattr(e, "winerror", None) == 10048:
                return False
            raise
    return True


def port_accepts_connections(port: int, host: str = DEFAULT_HOST) -> bool:
    """True if something answers on the port (connect probe, for verify-after-spawn)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def read_tracked_pid() -> int | None:
    """PID we previously wrote for a server we spawned, if any."""
    if not PID_FILE.is_file():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def process_is_alive(pid: int) -> bool:
    """Existence probe (psutil: uniform across Linux/macOS/Windows)."""
    return psutil.pid_exists(pid)


def server_is_running(port: int) -> bool:
    """True only if tracked PID is alive AND the port is occupied."""
    pid = read_tracked_pid()
    if pid is None:
        return False
    if not process_is_alive(pid):
        PID_FILE.unlink(missing_ok=True)  # stale: clean up
        return False
    return not port_is_free(port)


# Windows creation flags (subprocess only defines these constants on Windows,
# so the documented values are spelled out here): DETACHED_PROCESS = no
# console at all; CREATE_NEW_PROCESS_GROUP = immune to parent Ctrl+C.
_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200


def spawn_server(port: int) -> None:
    """Spawn the detached http server. Log and PID go to disk."""
    OUTPUT_ROOT.mkdir(exist_ok=True)
    if os.name == "nt":
        popen_kwargs: dict[str, int | bool] = {
            "creationflags": _DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP
        }
    else:
        popen_kwargs = {"start_new_session": True}  # POSIX setsid
    with SERVER_LOG.open("ab") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "http.server",
                str(port),
                "--bind",
                DEFAULT_HOST,
                "--directory",
                str(OUTPUT_ROOT),
            ],
            stdout=log,
            stderr=subprocess.STDOUT,  # without this a failure dies silently
            **popen_kwargs,
        )
    _ = PID_FILE.write_text(str(process.pid), encoding="utf-8")


def viewer_exists() -> bool:
    """True if the built frontend is published at output/index.html."""
    return (OUTPUT_ROOT / "index.html").is_file()


# Run-id timestamps are fs-safe local time by construction (`2026-10-08T22-27-06`);
# string normalization only — never datetime math, so no tz fabrication.
_RUN_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}")


def _run_timestamp(name: str) -> str | None:
    """Trailing timestamp segment of a run id (`run_<instance>_<ts>`), if it parses.

    Split from the right so instance names containing `_` stay safe.
    """
    ts = name.rsplit("_", 1)[-1]
    return ts if _RUN_TS_RE.fullmatch(ts) else None


def _iso_with_colons(ts: str) -> str:
    """`2026-10-08T22-27-06` (fs-safe) -> `2026-10-08T22:27:06` (ISO, Date-parseable)."""
    date, time = ts.split("T")
    return f"{date}T{time.replace('-', ':')}"


def write_run_index() -> None:
    """Scan output/runs/*/bnb_state.json -> runs/index.json (derived artifact).

    Entries are newest-first: sorted by the run id's trailing timestamp
    (instance name as tie-breaker), so index[0] — the frontend's fallback
    default — is truly the newest run. The write is atomic (tmp + os.replace):
    concurrent readers (http.server, the Vite dev middleware) can never see a
    torn file.
    """
    runs_dir = OUTPUT_ROOT / "runs"
    runs_dir.mkdir(exist_ok=True)

    json_paths = sorted(
        runs_dir.glob("*/bnb_state.json"),
        key=lambda p: (_run_timestamp(p.parent.name) or "", p.parent.name),
        reverse=True,
    )

    entries: list[dict[str, str | float | int | None]] = []
    for json_path in json_paths:
        try:
            data = BnBRunData.model_validate_json(json_path.read_bytes())
        except ValidationError as e:
            error = e.errors(include_url=False)[0]
            logger.warning(
                "Skipping corrupt run %s: %s: %s",
                json_path.parent.name,
                error["loc"],
                error["msg"],
            )
            continue
        # `date`: the run's own started_at (tz-aware ISO); runs exported
        # before that field existed fall back to their run-id timestamp.
        ts = _run_timestamp(json_path.parent.name)
        date = data.started_at or (_iso_with_colons(ts) if ts else None)
        entries.append(
            {
                "id": json_path.parent.name,
                "name": data.instance.name,
                "cost": data.best_solutions[-1].cost if data.best_solutions else None,
                "iterations": len(data.processing_order),
                "date": date,
            }
        )

    tmp_path = runs_dir / "index.json.tmp"
    tmp_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    os.replace(tmp_path, runs_dir / "index.json")


def _wait_until_serving(port: int) -> bool:
    """Poll the connect probe until the spawned server answers (or timeout)."""
    deadline = time.monotonic() + SPAWN_TIMEOUT_S
    while time.monotonic() < deadline:
        if port_accepts_connections(port):
            return True
        time.sleep(0.05)
    return False


def ensure_viewer() -> str | None:
    """Viewer publish check + server ensure. Returns base URL or None.

    Catalog regeneration is NOT done here — `write_run_index()` runs after a
    run dir is complete (see `BnBSerializer.save`), so a freshly opened tab can
    never see a catalog lacking its own run.
    """
    if not viewer_exists():
        logger.info("Viewer not published yet - run `just publish` once, then re-run.")
        return None

    port = resolve_port()

    if not server_is_running(port):
        if not port_is_free(port):
            logger.warning(
                "Port %s is already in use by something else - "
                "set BNB_VIEWER_PORT to pick a different port.",
                port,
            )
            return None
        spawn_server(port)
        if not _wait_until_serving(port):
            logger.warning(
                "Spawned viewer server did not come up within %.1fs.",
                SPAWN_TIMEOUT_S,
            )
            PID_FILE.unlink(missing_ok=True)
            return None

    return f"http://localhost:{port}"


def _pid_is_our_server(proc: psutil.Process, port: int) -> bool:
    """Guard against PID reuse: the process must be our http.server on our port.

    psutil reads the cmdline on every platform (no /proc dependency). On
    AccessDenied we trust the tracked PID — this is a same-user local tool,
    and stranding an unstoppable server is worse than a stale-pid risk.
    """
    try:
        args = [str(arg) for arg in proc.cmdline()]
    except psutil.AccessDenied:
        return True
    return "http.server" in args and str(port) in args


def stop_server() -> bool:
    """Stop the viewer server we spawned (never a foreign port occupant).

    Idempotent: nothing tracked or a stale entry both return False cleanly.
    """
    pid = read_tracked_pid()
    if pid is None:
        logger.info("No viewer server running.")
        return False
    if not psutil.pid_exists(pid):
        PID_FILE.unlink(missing_ok=True)  # stale entry, nothing to stop
        logger.info("Tracked viewer server already gone (cleaned stale PID file).")
        return False

    try:
        proc = psutil.Process(pid)
        if not _pid_is_our_server(proc, resolve_port()):
            PID_FILE.unlink(missing_ok=True)
            logger.warning(
                "Tracked PID %d no longer looks like our viewer server - "
                "removed the stale PID file without signaling.",
                pid,
            )
            return False
        # SIGTERM on POSIX; Windows terminate() is TerminateProcess (no
        # graceful phase exists there for a detached console-less process).
        proc.terminate()
        try:
            proc.wait(timeout=STOP_TIMEOUT_S)
        except psutil.TimeoutExpired:
            proc.kill()  # TERM was ignored: escalate
    except psutil.NoSuchProcess:
        pass  # died between the checks above

    # Unlink only if a concurrent save() has not replaced the entry meanwhile.
    if read_tracked_pid() == pid:
        PID_FILE.unlink(missing_ok=True)
    logger.info("Viewer server (pid %d) stopped.", pid)
    return True


def _main(argv: list[str]) -> int:
    if len(argv) > 1:
        if argv[1] == "stop":
            stop_server()
            return 0
        print(f"Unknown argument: {argv[1]}", file=sys.stderr)
        print("Usage: python -m tsp_bnb.export.viewer [stop]", file=sys.stderr)
        return 2
    base = ensure_viewer()
    if base is not None:
        write_run_index()
        print(base)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(_main(sys.argv))
