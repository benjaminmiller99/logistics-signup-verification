from src.infrai_client import InfraiClient


def test_create_user_does_not_reuse_email_as_idempotency_key():
    client = InfraiClient.__new__(InfraiClient)
    calls = []
    client.request = lambda method, path, body: calls.append((method, path, body))

    client.create_user("chenhua@changba.com", "password", "Operator")

    method, path, body = calls[0]
    assert (method, path) == ("POST", "/v1/auth/user/create")
    assert body["email"] == "chenhua@changba.com"
    assert "idempotency_key" not in body
