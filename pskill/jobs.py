"""jobs.py — Background process & scan job controller for Kali Linux."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config

JOBS_METADATA_FILE = config.JOBS_DIR / "jobs.json"


def _load_metadata() -> dict[str, dict[str, Any]]:
    config.ensure_dirs()
    if not JOBS_METADATA_FILE.exists():
        return {}
    try:
        return json.loads(JOBS_METADATA_FILE.read_text())
    except Exception:
        return {}


def _save_metadata(data: dict[str, dict[str, Any]]) -> None:
    config.ensure_dirs()
    JOBS_METADATA_FILE.write_text(json.dumps(data, indent=2) + "\n")


def is_pid_running(pid: int) -> bool:
    """Check if a process is actively running on Linux."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_job(cmd: str, desc: str = "", target: str = "", cwd: str | None = None) -> dict[str, Any]:
    """Start a long-running security tool / command in the background with redirected log output."""
    config.ensure_dirs()
    job_id = str(uuid.uuid4())[:8]
    log_path = config.JOBS_DIR / f"{job_id}.log"
    working_dir = os.path.expanduser(cwd) if cwd else os.getcwd()

    log_file = open(log_path, "w")
    start_time = datetime.now(timezone.utc).isoformat()

    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=working_dir,
        executable="/bin/bash",
        preexec_fn=os.setsid,  # Start a new process group for clean termination
    )

    job_info = {
        "id": job_id,
        "pid": proc.pid,
        "command": cmd,
        "description": desc or cmd,
        "target": target,
        "cwd": working_dir,
        "status": "running",
        "started": start_time,
        "log_path": str(log_path),
        "exit_code": None,
    }

    meta = _load_metadata()
    meta[job_id] = job_info
    _save_metadata(meta)

    return job_info


def list_jobs() -> list[dict[str, Any]]:
    """List all background jobs and sync active process states."""
    meta = _load_metadata()
    updated = False

    for job_id, job in meta.items():
        if job["status"] == "running":
            pid = job.get("pid", 0)
            if not is_pid_running(pid):
                job["status"] = "finished"
                updated = True

    if updated:
        _save_metadata(meta)

    return list(meta.values())


def get_job(job_id: str) -> dict[str, Any] | None:
    meta = _load_metadata()
    job = meta.get(job_id)
    if job and job["status"] == "running":
        if not is_pid_running(job.get("pid", 0)):
            job["status"] = "finished"
            _save_metadata(meta)
    return job


def kill_job(job_id: str) -> bool:
    """Kill a background job and its process group."""
    meta = _load_metadata()
    job = meta.get(job_id)
    if not job:
        return False

    pid = job.get("pid", 0)
    if is_pid_running(pid):
        try:
            # Kill process group
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            time.sleep(0.2)
            if is_pid_running(pid):
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

    job["status"] = "killed"
    _save_metadata(meta)
    return True


def tail_job(job_id: str, lines: int = 50) -> str:
    """Read the last N lines of a background job's log file."""
    job = get_job(job_id)
    if not job:
        return f"Job '{job_id}' not found."

    log_path = Path(job["log_path"])
    if not log_path.exists():
        return "(no log output yet)"

    try:
        content = log_path.read_text(errors="replace")
        all_lines = content.splitlines()
        tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return "\n".join(tail) or "(empty log)"
    except Exception as e:
        return f"Error reading log: {e}"
