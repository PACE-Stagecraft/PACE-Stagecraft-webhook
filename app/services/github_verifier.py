import hashlib
import hmac


def verify_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify the GitHub webhook HMAC-SHA256 signature.

    Args:
        payload_body: Raw request body bytes.
        signature_header: Value of the X-Hub-Signature-256 header (e.g. 'sha256=abcdef...').
        secret: The webhook secret string configured on the GitHub hook.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_sig = signature_header[len("sha256="):]
    computed_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed_sig, expected_sig)
