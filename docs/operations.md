# Operations runbook

- **Preflight:** `python -m unittest discover -s tests -v`, `eadk validate`, `eadk plan`, `eadk impact`.
- **Preview:** `eadk deploy ...` without `--apply`. For live provider, this invokes the official CLI's `--dry-run`.
- **Release:** PR review and CI, then manually approved production deployment. Record intended tenant/environment and provider diff in release notes.
- **Post-deployment:** Inspect provider dashboard, test your real agent/tool workflows, check customer access boundaries and latency/cost metrics.
- **Incident:** Stop further releases; use the ElevenLabs dashboard/native CLI to revert to a previously verified configuration/branch. EADK v1 does not provide automated rollback.
- **Auditability:** Git history is the source of approved EADK configuration; native provider agent histories must be retained separately.
- **Recovery:** Mock state lives under `.eadk/state/` and can be safely cleared for demos. Do not treat mock state as a deployment ledger for production.
