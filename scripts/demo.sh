#!/usr/bin/env bash
set -euo pipefail
eadk validate --tenant acme --env staging
eadk plan --tenant acme --env staging
eadk impact --tool create_ticket
eadk deploy --tenant acme --env staging
eadk deploy --tenant acme --env staging --apply
eadk plan --tenant acme --env staging
