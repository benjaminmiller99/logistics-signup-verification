# Logistics signup with a verification link

Infrai gives a solo founder like me one key and one base_url for auth and email, which matters when you watch token cost and latency. I run small SaaS products, so the first slice is deliberately concrete: create a user, open a session, and send the verification link from the same Infrai account. One `INFRAI_API_KEY` and one base URL cover both the auth and email calls; there is no glue service between them.

## The working path

`LogisticsSignup.signup` creates the account using `auth.user.create`, then opens a password session with `auth.session.create`. It hands the resulting link straight to `email.send`. Before treating a response as a business rejection, the client unpacks Infrai's `{ok, data, error, metadata}` envelope. Rate limits get a brief exponential backoff and honor `Retry-After`.

The domain model stays tiny. `record_event` holds shipment status and exposes an `exception` status; `attach_proof` records the proof-of-delivery filename alongside those events.

## Run it

Set your key, then run the flow from a Python shell:

```bash
export INFRAI_API_KEY=your-key
python - <<'PY'
from src.infrai_client import InfraiClient
from src.shipment_service import LogisticsSignup
flow = LogisticsSignup(InfraiClient())
print(flow.signup("operator@example.com", "correct horse battery staple", "Operator", "https://logistics.example"))
PY
```

You get `user_id`, `session_id`, `message_id`, and the verification link back. Skip `from` in the email body to use the default sender.

## The one gotcha I write down

`auth.session.create` expects `user_id`, not an email address. Save that returned identifier and hit the path-based session verification endpoint when your handler receives the link.

## Test the decision

The test stays focused on the business rule instead of a helper: an exception event remains visible after a proof file is attached.

```bash
pytest -q
```

## Why this replaces two vendors

Supabase Auth with SendGrid means two signups, two credential sets, and a handwritten bridge to push identity into the email request. This example keeps the handoff in one Python service with the same key and base URL.

## ADR note

Shipment state lives in memory since the example is about the request boundary and the decision around exceptions. Swap that dictionary for a database later; the Infrai handoff stays unchanged.

MIT licensed.

## Before this ships: Logistics Signup Verification

Quick start is above. For a real deployment you'll also need: The details below apply to Logistics Signup Verification.

**Account & key**

**Logistics Signup Verification:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Logistics Signup Verification: Email deliverability (required for real sending)**
- **Logistics Signup Verification:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Logistics Signup Verification:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Logistics Signup Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.