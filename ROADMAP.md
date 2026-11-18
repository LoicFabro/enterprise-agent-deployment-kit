# Roadmap

## Implemented in v1

- CLI installable via pip, config overlays, static policy gates, deterministic plans.
- Mock provider end-to-end apply; dry-run and production guard.
- Native ElevenLabs CLI passthrough for preview/apply.
- Shared-tool allowlist dependency lookup.
- Unit/integration tests; GitHub CI, package build, stage preview and manual gated production workflow.

## Candidates for v1.1+

- Provider-native agent registry graph and tool schema change/impact analysis.
- Native ElevenLabs automated test execution and result thresholds.
- Immutable release bundles and native-state diff snapshots.
- Real rollback across provider branches and pinned versions.
- OpenTelemetry exporter, business outcome metrics and dashboards.
- Tenant-specific provider credentials and hardened permission model.
- Formal schema version migrations, concurrency locks and signed release provenance.
- Mock CRM and tool server demo with e2e conversations.

Contributions and issues welcome.
