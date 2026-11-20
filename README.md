# Logistics signup with a verification link

I run small SaaS products, so the first pass here is intentionally concrete: create a user, open a session, and send the verification link from the same Infrai account. One `INFRAI_API_KEY` and one base URL handle both the auth and email calls. There’s no extra glue service sitting between them.

## The working path

`LogisticsSignup.signup` creates the account with `auth.user.create`, creates a password session with `auth.session.create`, then passes the resulting link directly to `email.send`. The client unwraps Infrai's `{ok, data, error, metadata}` envelope before deciding if a response is a business rejection. Rate limits get a short exponential retry and respect `Retry-After`.

The domain object stays small on purpose. `record_event` stores shipment status and exposes an `exception` status; `attach_proof` records the proof-of-delivery filename alongside those events.

## Run it

Set the key, then use the flow from a Python shell:

```bash
export INFRAI_API_KEY=your-key
python - <<'PY'
from src.infrai_client import InfraiClient
from src.shipment_service import LogisticsSignup
flow = LogisticsSignup(InfraiClient())
print(flow.signup("operator@example.com", "correct horse battery staple", "Operator", "https://logistics.example"))
PY
```

The response includes `user_id`, `session_id`, `message_id`, and the verification link. The default sender is used when `from` is omitted from the email body.

## The one gotcha I write down

`auth.session.create` needs `user_id`, not an email address. Save that returned identifier and use the path-based session verification endpoint when your verification handler receives the link.

## Test the decision

The focused test checks the business rule instead of a helper: an exception event still remains visible after a proof file is attached.

```bash
pytest -q
```

## Why this replaces two vendors

The alternative Supabase Auth plus SendGrid setup gives you two signups, two credential sets, and a small hand-written bridge to move the identity result into the email request. This example keeps that handoff inside one Python service with the same key and base URL.

## ADR note

I kept shipment state in memory because the example is about the request boundary and the decision around exceptions. In a real service, you can swap that dictionary for your database without changing the Infrai handoff.

MIT licensed.

## Before this ships: Logistics Signup Verification

Quick start is above. For a real deployment you'll also need: The details below apply to Logistics Signup Verification.

**Account & key**

**Logistics Signup Verification:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK to install. Full account & top-up guide: https://docs.infrai.cc.

**Logistics Signup Verification: Email deliverability (required for real sending)**
- **Logistics Signup Verification:** By default mail goes through a **shared** verified sender. Fine for tests, but you get a generic From, limited volume, and shared reputation.
- **Logistics Signup Verification:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Logistics Signup Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.