#!/usr/bin/env bash
# Deploy ForgeKit to Google Cloud Run (source-based build).
#
# After the first deploy, replace PLACEHOLDER in NEXT_PUBLIC_APP_URL with the
# real Cloud Run service URL (e.g. https://forgekit-xxxxx-rj.a.run.app) and
# re-run this script (or update the env var via gcloud run services update).
#
# Requires: gcloud authenticated and a project selected.
# Optional: ensure PATH includes /workspace/.gcloud/bin if using a local gcloud install.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="/workspace/.gcloud/bin:${PATH}"

gcloud run deploy forgekit --source . --region=southamerica-east1 --allow-unauthenticated \
  --set-env-vars="DEMO_MODE=true,DATABASE_URL=file:/tmp/forgekit.db,AUTH_SECRET=change-me,NEXT_PUBLIC_APP_URL=https://PLACEHOLDER"
