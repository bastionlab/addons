"""Designs on the host: publishing one to the marketplace catalogue (approve-then-Run, owner only) and
running "Describe a look" Claude jobs"""
import json, re, subprocess, time
from pathlib import Path

from dash_sdk import CLAUDE, action, alive, get, post, starttime, unit_pid

PUBLISH = str(Path(__file__).resolve().parent / "design-publish")


@action("design_publish")
def a_design_publish(args):
    """a design from /designs → `_designs/<login>-<name>.json` in the marketplace repo, as a design/<slug> PR that
    GitHub checks (colours only, the publisher's own file) and merges; every install then lists it"""
    did = str(args.get("id", ""))
    if not did.isdigit():
        raise ValueError("bad design id")
    name = str(args.get("name", "")).strip()[:40] or f"design {did}"
    return (f"publish the design “{name}” (colours, stylesheet, skin) to the marketplace catalogue under your GitHub login: "
            f"GitHub checks it holds only colours, a safe stylesheet (nothing loaded from outside) and a skin name, then merges it.",
            ["python3", "-I", PUBLISH, did], 1800)


# "Describe a look": a tool-less `claude -p` with a JSON schema in its own unit (survives an agent restart);
# the dashboard owns the prompt and checks the answer, this only runs it and hands the structured output back
AI_DIR = Path("/var/lib/dash-designs")


def _unit(job):
    if not re.fullmatch(r"[a-f0-9]{16}", job or ""):
        raise ValueError("bad job id")
    return f"dash-design-{job}"


@post("/designs/ai/start")
def ai_start(body):
    job, prompt, schema = str(body.get("job")), body.get("prompt"), body.get("schema")
    unit = _unit(job)
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 60_000 or not isinstance(schema, dict):
        raise ValueError("bad prompt or schema")
    AI_DIR.mkdir(mode=0o700, exist_ok=True)
    for f in AI_DIR.glob("*"):
        if f.stat().st_mtime < time.time() - 2 * 86400:
            f.unlink(missing_ok=True)
    (AI_DIR / f"{job}.prompt").write_text(prompt)
    cmd = [CLAUDE, "-p", "--model", "sonnet", "--effort", "medium", "--no-session-persistence", "--tools", "",
           "--output-format", "json", "--json-schema", json.dumps(schema)]
    r = subprocess.run(["systemd-run", "--unit", unit, "--collect", "--quiet", "-p", "WorkingDirectory=/tmp",
                        "-p", f"StandardInput=file:{AI_DIR / f'{job}.prompt'}",
                        "-p", f"StandardOutput=file:{AI_DIR / f'{job}.out'}", "-p", f"StandardError=file:{AI_DIR / f'{job}.err'}",
                        "-p", "RuntimeMaxSec=15min",
                        "-E", "HOME=/root", "-E", "CLAUDE_PROFILE=noven", "-E", "TERM=dumb",
                        "-E", "PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                        *cmd], capture_output=True, text=True, timeout=20)
    if r.returncode:
        raise ValueError(f"could not start claude: {r.stderr.strip()[:300]}")
    pid = unit_pid(unit)
    (AI_DIR / f"{job}.json").write_text(json.dumps({"pid": pid, "t0": starttime(pid), "started": time.time()}))
    return {"job": job, "running": True}


@get("/designs/ai/job", quiet=True)
def ai_job(q):
    job = str(q.get("id"))
    _unit(job)
    meta = AI_DIR / f"{job}.json"
    if not meta.exists():
        return {"state": "gone"}
    m = json.loads(meta.read_text())
    if alive(m):
        return {"state": "running", "secs": int(time.time() - m["started"])}
    out, err = AI_DIR / f"{job}.out", AI_DIR / f"{job}.err"
    try:
        r = json.loads(out.read_text())
    except (OSError, ValueError):
        tail = err.read_text(errors="replace")[-400:] if err.exists() else ""
        return {"state": "failed", "error": tail.strip() or "claude stopped without an answer"}
    if r.get("is_error") or not isinstance(r.get("structured_output"), dict):
        return {"state": "failed", "error": str(r.get("result") or r.get("subtype") or "no structured answer")[:400]}
    return {"state": "done", "result": r["structured_output"], "secs": int(r.get("duration_ms", 0) / 1000)}
