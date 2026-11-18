# Enterprise Agent Deployment Kit (EADK) v1.0.1

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-informational)](.github/workflows/ci.yml) [![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](pyproject.toml) [![License](https://img.shields.io/badge/License-Apache--2.0-blue)](LICENSE)

**Governed AI agent deployments across customers and environments.** EADK is a small, runnable deployment-orchestration layer around provider-native agent tooling. It offers configuration overlays, deployment validation, deterministic plans, policy checks, shared-tool impact analysis, and explicitly gated deploys. An offline mock provider means the entire toolkit can be evaluated without credentials or spending money.

> **Scope / verification:** The local mock workflow and automated tests have been executed. Live ElevenLabs deployment requires your own ElevenLabs account, API key, official CLI, and native agent project; it has **not** been live-tested without those credentials. EADK intentionally delegates agent synchronization to the official ElevenLabs CLI rather than reimplementing provider API schemas. This project is an engineering reference implementation, not an independently certified security/compliance product.

## Python 3.9 compatibility

EADK v1.0.1 supports **Python 3.9 and later**. It uses only Python standard-library runtime dependencies. The package build requires a Python-3.9-compatible setuptools release, which pip's build isolation selects automatically. CI tests Python 3.9, 3.10, 3.12, and 3.13.

On macOS, recreate an environment if it was built using another Python version:

```bash
# From the extracted project directory
# Leave the current environment if active
deactivate 2>/dev/null || true
rm -rf .venv
/usr/bin/python3 -m venv .venv  # only if /usr/bin/python3 --version is 3.9
source .venv/bin/activate
python --version
python -m pip install -e .
```

For Homebrew installations, replace `/usr/bin/python3` with the exact desired Homebrew Python executable. You can also keep an existing functioning Python 3.9 `.venv` and just install the upgraded package.

## Quick start (no API keys)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
eadk validate --tenant acme --env staging
eadk plan --tenant acme --env staging
eadk impact --tool create_ticket
eadk deploy --tenant acme --env staging          # dry-run; no writes
eadk deploy --tenant acme --env staging --apply  # local mock state only
eadk plan --tenant acme --env staging          # NO_CHANGE
python -m unittest discover -s tests -v
```

On Windows, activate `.venv\\Scripts\\activate` instead. Python 3.9+ required. Python 3.9 is legacy/end-of-life; modern versions are recommended for live production deployment.

## CLI

| Command | Behavior |
| --- | --- |
| `eadk init` | Create a new synthetic mock project in empty root; non-destructive |
| `eadk validate --tenant T --env E` | Enforce static configuration and deployment policy checks; nonzero on errors |
| `eadk plan --tenant T --env E` | Show canonical config fingerprint and local state difference |
| `eadk impact --tool NAME` | List all tenant/environment configs using a named tool |
| `eadk deploy --tenant T --env E` | Dry-run provider action, no local or remote writes |
| `eadk deploy --tenant T --env E --apply` | Apply mock state or invoke official ElevenLabs push |
| `eadk test` | Run portable offline package smoke checks; full suite via unittest |

All CLI commands accept `--project /path/to/project` **before** their subcommand. Config formats are JSON. Base tenant configuration merges recursively with `development.json`, `staging.json`, or `production.json`; arrays replace rather than append. Credentials must be environment references or supplied directly to provider processes via environment variables.

## What's included

- Two synthetic customers (`acme`, `contoso`), including distinct stage/prod settings.
- Deep-merge resolution and deterministic SHA-256 plan fingerprints.
- Fail-closed policy checks (tenant identity, environment, credentials, auth flag, redaction flag, audit flag, tool allowlists, production approvals, testing requirements).
- Static shared-tool blast radius analysis across tenant environments.
- Offline mock provider for reproducible deployment lifecycle tests.
- ElevenLabs provider adapter executing `elevenlabs agents push --dry-run` or `elevenlabs agents push` in its **native** project directory.
- Automated CI, build artifacts, staging dry-run and manual production workflow.

## Project layout

```text
src/eadk/          Python CLI, policy, plan, provider adapter
tests/             Unit and offline integration tests
tenants/           Customer base/environment overlays
docs/              Architecture, security, ElevenLabs setup, operations
.github/workflows/ CI, package build, stage preview, guarded production
scripts/           Demo script
.eadk/state/       Mock applied state (gitignored)
```

## ElevenLabs live setup

See [docs/elevenlabs.md](docs/elevenlabs.md). Install the official CLI, initialize a **native ElevenLabs agent project** in `elevenlabs/`, add/configure at least one agent, then change `provider` to `elevenlabs` and set `native_project` to `elevenlabs` in the desired tenant/environment overlay. EADK's tenant overlays control **governance metadata**, not arbitrary native agent fields. The native project remains the source of truth for actual agent configuration. In this v1 implementation, a native project is mapped to its own deployment context. Do not point multiple tenants at one native project unless you explicitly intend the same agent registry and credentials to be deployed for both.

**No live deployment is performed by CI by default.** Manual production workflow requires a GitHub Environment `production` with required reviewers and an `ELEVENLABS_API_KEY` secret. Configure your native agent project before running it.

## Limitations / non-goals

- The mock provider is a local state writer, **not** a simulated voice conversation or CRM integration.
- The project checks configured security declarations but does not prove that PII is redacted, authorization is enforced at runtime, or a tool is safe. Those must be implemented/tested by your deployed tool service.
- Fingerprints cover EADK JSON configuration, **not** the full native ElevenLabs agent registry. Provider CLI dry-run is required for native diffs.
- `impact` statically examines EADK allowlists. It is not a complete provider dependency graph.
- There is no automatic agent rollback, multi-region orchestration, runtime telemetry, or native ElevenLabs test-suite execution in v1. See [ROADMAP.md](ROADMAP.md).
- Do not put secrets, customer data, private prompts, or production identifiers in the repo.

## GitHub publishing

1. Create an empty GitHub repository.
2. Unzip, `git init`, `git add .`, `git commit -m 'Initial EADK v1'`.
3. Add your GitHub remote and `git push -u origin main`.
4. Enable GitHub Actions. Configure `production` Environment with **required reviewers** before using the production workflow.
5. Read [SECURITY.md](SECURITY.md) before adding any real data or credentials.

## Attribution

Independent community project, not affiliated with or endorsed by ElevenLabs. Uses the official CLI if you choose live deployment. Licensed Apache-2.0; see [LICENSE](LICENSE).
