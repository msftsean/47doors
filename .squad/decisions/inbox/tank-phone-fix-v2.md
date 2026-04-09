# Decision: Fix ACS CallbackUri for Container Apps

**Date:** 2026-04-09
**Author:** Tank
**Status:** Implemented & deployed

## Context

Inbound phone calls to +19132171946 were not being answered. After the SDK import fix (a885b62), calls still failed with `(400) The field CallbackUri is invalid`. The callback URL was constructed from `request.base_url`, which inside Azure Container Apps resolves to an internal `http://` URL. ACS requires HTTPS.

## Decision

1. Reconstruct callback URL from `X-Forwarded-Proto` + `Host` request headers (set by Container Apps ingress).
2. Added `PHONE_CALLBACK_BASE_URL` config setting as explicit override.
3. Set the env var on the container app as belt-and-suspenders.

## Consequences

- Phone calls will now be answered correctly when Event Grid delivers IncomingCall events.
- Any future service that needs a public callback URL should follow the same pattern (check forwarded headers, support explicit config override).
- The health endpoint still only tests client init, not the full answer_call flow — team should be aware that "healthy" doesn't mean "calls work."

## Files Changed

- `backend/app/api/phone.py` — callback URL reconstruction
- `backend/app/core/config.py` — `phone_callback_base_url` field
- Container env: `PHONE_CALLBACK_BASE_URL` set on `frontdoor-tlijy2xjo4fvg-backend`
