"""Pure, offline-safe planning and validation logic."""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

class EADKError(Exception):
    pass

def read_json(path: Path) -> dict:
    if not path.is_file():
        raise EADKError(f"Missing file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise EADKError(f"Invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EADKError(f"JSON root must be an object: {path}")
    return value

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def safe_identifier(s: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", s):
        raise EADKError(f"Invalid identifier {s!r}; use lower-case letters, numbers and hyphens")
    return s

def merge(base: dict, overlay: dict) -> dict:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result

def project_root(start: Path) -> Path:
    p = start.resolve()
    if not (p / "eadk.json").is_file():
        raise EADKError(f"No eadk.json at {p}; pass --project or run eadk init")
    return p

@dataclass(frozen=True)
class Deployment:
    root: Path
    tenant: str
    environment: str
    config: dict
    manifest: dict
    fingerprint: str

def load(root: Path, tenant: str, environment: str) -> Deployment:
    root = project_root(root)
    safe_identifier(tenant)
    if environment not in {"development", "staging", "production"}:
        raise EADKError("Environment must be development, staging, or production")
    manifest = read_json(root / "eadk.json")
    base = read_json(root / "tenants" / tenant / "base.json")
    overlay = read_json(root / "tenants" / tenant / f"{environment}.json")
    config = merge(base, overlay)
    config.setdefault("tenant", tenant)
    config.setdefault("environment", environment)
    return Deployment(root, tenant, environment, config, manifest, digest(config))

@dataclass
class Finding:
    code: str
    level: str
    message: str

SECRET_FIELD = re.compile(r"(^|_)(api[_-]?key|secret|password|private[_-]?key|access[_-]?token)(_|$)", re.I)
SENSITIVE_LITERAL = re.compile(r"(?:sk_[A-Za-z0-9]{14,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")

def findings(d: Deployment) -> list[Finding]:
    c = d.config
    out: list[Finding] = []
    def fail(code: str, message: str): out.append(Finding(code, "ERROR", message))
    def warn(code: str, message: str): out.append(Finding(code, "WARN", message))
    if c.get("tenant") != d.tenant or c.get("environment") != d.environment:
        fail("IDENTITY", "Resolved tenant/environment does not match target")
    if not isinstance(c.get("agent"), dict) or not c["agent"].get("name"):
        fail("AGENT", "agent.name is required")
    provider = c.get("provider")
    if provider not in ("mock", "elevenlabs"):
        fail("PROVIDER", "provider must be mock or elevenlabs")
    sec = c.get("security", {})
    if not isinstance(sec, dict):
        fail("SECURITY", "security must be an object")
        sec = {}
    for field in ("require_authentication", "audit_logging", "pii_redaction"):
        if sec.get(field) is not True:
            fail("SECURITY_" + field.upper(), f"security.{field} must be true")
    if not isinstance(sec.get("allowed_tools"), list) or not sec.get("allowed_tools"):
        fail("TOOLS", "security.allowed_tools must be a non-empty list")
    if len(sec.get("allowed_tools", [])) != len(set(map(str, sec.get("allowed_tools", [])))):
        fail("TOOLS_DUPLICATE", "Tool allowlist contains duplicate entries")
    gov = c.get("governance", {})
    if not isinstance(gov, dict):
        gov = {}; fail("GOVERNANCE", "governance must be an object")
    if d.environment == "production" and gov.get("require_approval") is not True:
        fail("APPROVAL", "Production must require manual approval")
    if d.environment == "production" and gov.get("tests_required") is not True:
        fail("TESTING", "Production must require automated tests")
    if not c.get("integrations") or not isinstance(c.get("integrations"), dict):
        warn("INTEGRATIONS", "No integration map configured")
    if provider == "elevenlabs":
        native = c.get("native_project", "elevenlabs")
        path = (d.root / native).resolve()
        if not path.is_relative_to(d.root) or not (path / "agents.json").is_file():
            fail("NATIVE_PROJECT", "ElevenLabs provider requires an initialized native project with agents.json")
    def walk(value: Any, path: str = ""):
        if isinstance(value, dict):
            for k, v in value.items():
                keypath = f"{path}.{k}" if path else k
                if SECRET_FIELD.search(k) and isinstance(v, str) and v and not v.startswith("env:"):
                    fail("EMBEDDED_SECRET", f"Potential embedded credential at {keypath}; use env:VARIABLE")
                walk(v, keypath)
        elif isinstance(value, list):
            for i, v in enumerate(value): walk(v, f"{path}[{i}]")
        elif isinstance(value, str) and SENSITIVE_LITERAL.search(value):
            fail("SECRET_PATTERN", f"Sensitive value pattern at {path}")
    walk(c)
    return out

def dependency_impact(root: Path, tool: str) -> list[dict]:
    safe_identifier(tool.replace("_", "-"))
    rows = []
    for directory in sorted((root / "tenants").glob("*")):
        if not directory.is_dir() or not (directory / "base.json").is_file():
            continue
        for env in ("development", "staging", "production"):
            if not (directory / f"{env}.json").is_file():
                continue
            d = load(root, directory.name, env)
            if tool in d.config.get("security", {}).get("allowed_tools", []):
                rows.append({"tenant": d.tenant, "environment": env, "agent": d.config.get("agent", {}).get("name"), "risk": "HIGH" if env == "production" else "MEDIUM"})
    return rows

def plan(d: Deployment) -> dict:
    state_file = d.root / ".eadk" / "state" / d.tenant / f"{d.environment}.json"
    prev = read_json(state_file) if state_file.is_file() else {}
    previous = prev.get("fingerprint")
    return {"tenant": d.tenant, "environment": d.environment, "provider": d.config.get("provider"), "fingerprint": d.fingerprint, "previous_fingerprint": previous, "change": "NO_CHANGE" if previous == d.fingerprint else ("CREATE" if not previous else "UPDATE"), "validation": [f.__dict__ for f in findings(d)]}
