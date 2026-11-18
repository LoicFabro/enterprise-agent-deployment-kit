"""eadk command line interface; no network calls without explicit deploy action."""
import argparse
import json
import os
import sys
import unittest
from pathlib import Path
from .core import EADKError, dependency_impact, findings, load, plan, project_root
from .providers import deploy

def output(value):
    print(json.dumps(value, indent=2, sort_keys=True))

def build_parser():
    p = argparse.ArgumentParser(prog="eadk", description="Enterprise Agent Deployment Kit v1")
    p.add_argument("--project", default=".", help="Root containing eadk.json")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Scaffold a local mock project")
    for name in ("validate", "plan", "deploy"):
        x = sub.add_parser(name)
        x.add_argument("--tenant", default="acme")
        x.add_argument("--env", dest="environment", default="staging", choices=["development", "staging", "production"])
        if name == "deploy":
            x.add_argument("--apply", action="store_true", help="Perform writes (dry run by default)")
            x.add_argument("--approve-production", action="store_true", help="Human production approval, only accepted interactively")
    sub.add_parser("test", help="Run built-in unit/integration tests (offline)")
    x = sub.add_parser("impact", help="List customer/environment references to a tool")
    x.add_argument("--tool", required=True)
    return p

def scaffold(root: Path):
    if (root / "eadk.json").exists():
        raise EADKError("Project already exists; init will not overwrite")
    (root / "tenants" / "acme").mkdir(parents=True, exist_ok=True)
    def write(relative, value):
        p = root / relative
        p.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    write("eadk.json", {"schema_version": 1, "project": "my-enterprise-agents"})
    write("tenants/acme/base.json", {"provider": "mock", "agent": {"name": "Demo Support Agent"}, "security": {"require_authentication": True, "audit_logging": True, "pii_redaction": True, "allowed_tools": ["get_ticket", "create_ticket"]}, "governance": {"require_approval": True, "tests_required": True}, "integrations": {"crm": "synthetic"}})
    for env in ("development", "staging", "production"):
        write(f"tenants/acme/{env}.json", {"environment": env})
    return {"project": str(root), "message": "Created local mock project"}

def local_tests():
    # Check repository tests when invoked from the repository, otherwise smoke-test the library.
    from .core import merge, digest
    assert merge({"a": {"b": 1}}, {"a": {"c": 2}}) == {"a": {"b": 1, "c": 2}}
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})
    return {"passed": 2, "message": "Offline package smoke tests passed; run python -m unittest discover -s tests -v for full suite"}

def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.project).resolve()
        if args.command == "init":
            output(scaffold(root)); return 0
        if args.command == "test":
            output(local_tests()); return 0
        root = project_root(root)
        if args.command == "impact":
            output({"tool": args.tool, "dependents": dependency_impact(root, args.tool)}); return 0
        d = load(root, args.tenant, args.environment)
        bad = [f for f in findings(d) if f.level == "ERROR"]
        if args.command == "validate":
            output({"valid": not bad, "fingerprint": d.fingerprint, "findings": [f.__dict__ for f in findings(d)]})
            return 2 if bad else 0
        if args.command == "plan":
            output(plan(d)); return 2 if bad else 0
        if bad:
            raise EADKError("Deployment blocked: " + "; ".join(f.message for f in bad))
        if args.apply and d.environment == "production":
            if os.environ.get("GITHUB_ACTIONS") == "true":
                if os.environ.get("EADK_PRODUCTION_APPROVED") != "true":
                    raise EADKError("Production deployment requires GitHub environment approval (EADK_PRODUCTION_APPROVED=true)")
            elif not (args.approve_production and sys.stdin.isatty()):
                raise EADKError("Production apply requires --approve-production from an interactive terminal")
        result = deploy(d, args.apply)
        output(result)
        return 0
    except EADKError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
