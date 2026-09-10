#!/usr/bin/env bash
# Update an existing service; bootstrap, IAM and secrets are managed separately.
set -euo pipefail
: "${GCP_PROJECT_ID:?Set the confirmed AnderZilla project ID}"
: "${GCP_REGION:?Set the service region}"
: "${GCP_SERVICE:?Set the existing ForgeKit service name}"
: "${IMAGE_DIGEST:?Set the complete Artifact Registry image with sha256 digest}"
[[ "$GCP_PROJECT_ID" =~ ^anderzilla-[a-z0-9-]+$ ]] || { echo 'Expected an AnderZilla project.' >&2; exit 1; }
[[ "$GCP_REGION" =~ ^[a-z]+-[a-z]+[0-9]+$ ]] || { echo 'Invalid region.' >&2; exit 1; }
[[ "$GCP_SERVICE" =~ ^forgekit(-[a-z0-9-]+)?$ ]] || { echo 'Expected a ForgeKit service.' >&2; exit 1; }
expected="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/anderzilla/forgekit@sha256:"
[[ "$IMAGE_DIGEST" == "$expected"* ]] || { echo 'Image must belong to the target project registry.' >&2; exit 1; }
[[ "${IMAGE_DIGEST#"$expected"}" =~ ^[a-f0-9]{64}$ ]] || { echo 'Invalid image digest.' >&2; exit 1; }
account='player.one@anderzilla.com'
if compgen -e | grep -q '^CLOUDSDK_AUTH_'; then
  echo 'Remove inherited CLOUDSDK_AUTH overrides first.' >&2; exit 1
fi
for property in impersonate_service_account access_token_file credential_file_override; do
  override="$(gcloud --configuration=anderzilla config get-value "auth/$property" 2>/dev/null)"
  [[ -z "$override" || "$override" == '(unset)' ]] || { echo 'Remove gcloud credential/impersonation overrides first.' >&2; exit 1; }
done
actual="$(gcloud --configuration=anderzilla config get-value account 2>/dev/null)"
[[ "$actual" == "$account" ]] || { echo 'Authenticate the authorized AnderZilla account first.' >&2; exit 1; }
gcloud --configuration=anderzilla --account="$account" --project="$GCP_PROJECT_ID" run services describe "$GCP_SERVICE" --region="$GCP_REGION" --format='value(metadata.name)'
gcloud --configuration=anderzilla --account="$account" --project="$GCP_PROJECT_ID" run services update "$GCP_SERVICE" --region="$GCP_REGION" --image="$IMAGE_DIGEST" --quiet
