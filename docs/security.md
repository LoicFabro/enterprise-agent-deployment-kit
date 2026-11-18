# Security model

Static EADK checks enforce declarations for authentication, redaction, audit logging, least-privilege tool allowlists, approval and test gates. These checks do NOT implement or verify runtime security. Protect API keys using process environment variables or GitHub Actions secrets. Avoid deploying the demo registry to customer workspaces.

## Threats and mitigations

| Risk | Mitigation / remaining gap |
|---|---|
| Secret checked into configs | Embedded secret key detection; GitHub secret scanning recommended. No guarantee every secret pattern will be caught. |
| Unauthorized tool call | Explicit tool allowlist declaration; actual tool server must enforce authorization. |
| Cross-tenant leakage | Per-tenant config and planned separate native registries; runtime isolation not provided by EADK. |
| Unsafe prod push | Manual CLI flag, interactive requirement or protected GitHub Environment. Repo administrators must configure reviewers. |
| Malicious PR editing deployment scripts | GitHub Environment protection, trusted review and branch protections; review workflows carefully. |
| Provider CLI leaking output | CLI stdout suppressed; errors report only return codes. Direct CLI troubleshooting may output sensitive data. |
| Drift between config and provider | Native CLI dry-run must be inspected; EADK fingerprint intentionally covers overlays only. |

Security deployment checklists should be reviewed by your organization's security/compliance teams. This toolkit does not certify compliance with SOC 2, HIPAA, FedRAMP, PCI DSS, or other standards.
