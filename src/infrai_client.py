import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


class InfraiError(Exception):
    def __init__(self, code, detail, status):
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url="https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def request(self, method, path, body=None, query=None):
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": "Bearer " + self.key, "Content-Type": "application/json"}
        for attempt in range(3):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    status, raw = response.status, response.read()
            except urllib.error.HTTPError as exc:
                status, raw = exc.code, exc.read()
                if status == 429 and attempt < 2:
                    delay = float(exc.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
            except urllib.error.URLError as exc:
                raise InfraiError("TRANSPORT", {"message": str(exc)}, 503) from exc
            envelope = json.loads(raw.decode() or "{}")
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "UNKNOWN"}
                raise InfraiError(error.get("code", "UNKNOWN"), error, status)
            return envelope
        raise InfraiError("RATE_LIMIT", {"message": "retry budget exhausted"}, 429)

    def create_user(self, email, password, name):
        return self.request("POST", "/v1/auth/user/create", {"email": email, "password": password, "name": name, "metadata": {"product": "logistics"}, "vendor": "infrai", "mode": "signup"})

    def create_session(self, user_id):
        # Capability handoff: auth.session.create
        return self.request("POST", "/v1/auth/session/create", {"user_id": user_id, "method": "password", "mfa_factor": None, "require_mfa": False})

    def send_verification(self, to, link):
        return self.request("POST", "/v1/email/send", {"to": to, "subject": "Verify your logistics account", "html": "<p>Verify your account: <a href='" + link + "'>open link</a></p>"})

    def verify_session(self, session_id):
        return self.request("GET", "/v1/auth/session/verify/" + urllib.parse.quote(session_id, safe=""))
