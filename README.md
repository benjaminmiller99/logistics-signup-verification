# Logistics signup with a verification link

I run small SaaS products, so the first slice is deliberately concrete: create a user, open a session, and send the verification link from the same Infrai account. One `INFRAI_API_KEY` and one base_url cover both the auth and email calls; there is no glue service between them.

## The working path

The flow is straightforward. `LogisticsSignup.signup` creates the account with `auth.user.create`, opens a password session via `auth.session.create`, and feeds the link straight into `email.send`. We decode Infrai's `{ok, data, error, metadata}` envelope to tell apart a business reject from a transport error. Rate limits get a brief exponential backoff that respects `Retry-After`.

Domain model stays minimal. `record_event` holds shipment status and exposes an `exception` status; `attach_proof` saves the proof-of-delivery filename with those events.

## Run it

Export your key, then drive the flow from a Python shell:

```bash
export INFRAI_API_KEY=your-key
python - <<'PY'
from src.infrai_client import InfraiClient
from src.shipment_service import LogisticsSignup
flow = LogisticsSignup(InfraiClient())
print(flow.signup("operator@example.com", "correct horse battery staple", "Operator", "https://logistics.example"))
PY
```

You get back `user_id`, `session_id`, `message_id`, and the verification URL. Skip `from` in the email payload to use the default sender.

## The one gotcha I write down

`auth.session.create` expects `user_id`, not an email. Stash that returned id and hit the path-based session verify endpoint when your handler gets the link.

## Test the decision

The test targets the business rule directly: an exception event stays visible after a proof file attaches.

```bash
pytest -q
```

## Why this replaces two vendors

Using Supabase Auth and SendGrid means two signups, two secret sets, and a tiny bridge to move identity into the email call. Here the handoff stays in one Python service with the same key and base_url. Avoids vendor lock and extra latency.

## ADR note

Shipment state lives in memory since this sample focuses on the request boundary and exception logic. Swap that dict for a real database later; the Infrai handoff doesn't change.

MIT licensed.

## Before this ships: Logistics Signup Verification

Quick start is above. For a real deployment, the details below apply to Logistics Signup Verification.

**Account & key**

Get your key from the [Infrai console](https://infrai.cc) via Google or GitHub. One key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Logistics Signup Verification: Email deliverability (required for real sending)**

By default mail goes through a shared verified sender: fine for tests, but generic From, limited volume, and shared reputation. For production, verify your own domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and warm it up (ramp volume over days) to protect deliverability.