"""Tests for GitHub webhook HMAC-SHA256 signature verification."""
import hashlib
import hmac

from app.services.github_verifier import verify_signature

SECRET = "test-webhook-secret"


def _make_sig(body: bytes, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_signature_accepted():
    body = b'{"action": "completed"}'
    sig = _make_sig(body)
    assert verify_signature(body, sig, SECRET) is True


def test_wrong_secret_rejected():
    body = b'{"action": "completed"}'
    sig = _make_sig(body, secret="wrong-secret")
    assert verify_signature(body, sig, SECRET) is False


def test_missing_signature_rejected():
    body = b'{"action": "completed"}'
    assert verify_signature(body, "", SECRET) is False


def test_no_sha256_prefix_rejected():
    body = b'{"action": "completed"}'
    raw = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, raw, SECRET) is False


def test_tampered_body_rejected():
    original = b'{"action": "completed"}'
    tampered = b'{"action": "completed", "injected": true}'
    sig = _make_sig(original)
    assert verify_signature(tampered, sig, SECRET) is False


def test_timing_safe_compare(monkeypatch):
    """verify_signature must use compare_digest (not ==) — confirm it's called."""
    body = b"payload"
    sig = _make_sig(body)
    calls = []
    original = hmac.compare_digest

    def spy(a, b):
        calls.append((a, b))
        return original(a, b)

    monkeypatch.setattr(hmac, "compare_digest", spy)
    verify_signature(body, sig, SECRET)
    assert len(calls) == 1, "compare_digest must be called exactly once"
