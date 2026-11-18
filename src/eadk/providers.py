"""Provider implementations. ElevenLabs is delegated to its maintained official CLI."""
import json
import os
import shutil
import subprocess
from pathlib import Path
from .core import Deployment, EADKError

def run_native(d: Deployment, apply: bool) -> dict:
    native = (d.root / d.config.get("native_project", "elevenlabs")).resolve()
    if not native.is_relative_to(d.root) or not (native / "agents.json").is_file():
        raise EADKError("Native ElevenLabs project missing or escapes project root")
    executable = shutil.which("elevenlabs")
    if not executable:
        raise EADKError("Official ElevenLabs CLI not installed. See docs/elevenlabs.md")
    if apply and not os.environ.get("ELEVENLABS_API_KEY"):
        raise EADKError("ELEVENLABS_API_KEY is required for noninteractive deployment")
    cmd = [executable, "agents", "push"]
    if not apply:
        cmd.append("--dry-run")
    try:
        completed = subprocess.run(cmd, cwd=native, capture_output=True, text=True, timeout=120, check=False)
    except subprocess.TimeoutExpired as exc:
        raise EADKError("ElevenLabs command timed out") from exc
    # Do not print raw command output because the provider could echo user-specific values.
    if completed.returncode:
        raise EADKError(f"ElevenLabs CLI failed (exit {completed.returncode}). Run 'elevenlabs agents push --dry-run' locally to troubleshoot")
    return {"provider": "elevenlabs", "mode": "apply" if apply else "dry-run", "exit_code": completed.returncode, "message": "Official ElevenLabs CLI completed"}

def deploy_mock(d: Deployment, apply: bool) -> dict:
    state_file = d.root / ".eadk" / "state" / d.tenant / f"{d.environment}.json"
    if apply:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"tenant": d.tenant, "environment": d.environment, "fingerprint": d.fingerprint, "agent": d.config["agent"]["name"]}
        state_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {"provider": "mock", "mode": "apply" if apply else "dry-run", "fingerprint": d.fingerprint, "message": "State written locally" if apply else "No writes performed"}

def deploy(d: Deployment, apply: bool) -> dict:
    if d.config.get("provider") == "mock":
        return deploy_mock(d, apply)
    if d.config.get("provider") == "elevenlabs":
        return run_native(d, apply)
    raise EADKError("Unknown provider")
