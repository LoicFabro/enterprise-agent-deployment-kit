# ElevenLabs integration

The official ElevenLabs CLI owns the *native agents-as-code registry*. EADK adds tenant/environment policy checks around the native synchronization workflow.

Reference: https://elevenlabs.io/docs/eleven-agents/operate/cli

## One-time setup

1. Install the ElevenLabs CLI (for example, `npm install -g @elevenlabs/cli` or `brew install elevenlabs/tap/elevenlabs`). Verify `elevenlabs --help` works.
2. From repository root, run `elevenlabs agents init elevenlabs`.
3. Run `cd elevenlabs && elevenlabs agents add "Acme Support" --template customer-service --skip-upload` (check `elevenlabs agents add --help` if your CLI release differs).
4. Set `provider` to `elevenlabs` and `native_project` to `elevenlabs` in your target tenant overlay JSON. The sample project ships in mock mode on purpose.
5. Set `ELEVENLABS_API_KEY` in your shell or configured CI environment. Never add credentials to JSON or commit `.env`.
6. Run `eadk validate --tenant acme --env staging`; then `eadk deploy --tenant acme --env staging` (official CLI dry-run); review changes.
7. Finally use `eadk deploy --tenant acme --env staging --apply` to push agent changes.

**Important:** `agents push` synchronizes the *entire native CLI project*. EADK does **not** automatically isolate native registries per tenant; use a distinct project/workspace per tenant or deliberately control the shared registry. A given `native_project` directory is the sole source of truth for which agent definitions will be pushed. Agent versioning/branch semantics depend on official CLI and account capabilities.

## Production

Production application is additionally gated by either:
- Local interactive terminal and `--approve-production`, or
- A GitHub Actions job with `GITHUB_ACTIONS=true` and `EADK_PRODUCTION_APPROVED=true`, which **must** be protected by a `production` GitHub Environment requiring reviewers.

Example (manual local production):

```bash
eadk validate --tenant acme --env production
eadk deploy --tenant acme --env production          # preview only
eadk deploy --tenant acme --env production --apply --approve-production
```

**Note:** This release invokes `elevenlabs agents push --dry-run` for preview and `elevenlabs agents push` for application. Their behavior and flags were checked against the published CLI documentation, not executed against a live account in this build. Native CLI errors are deliberately not echoed to avoid exposing secrets; reproduce directly when debugging.
