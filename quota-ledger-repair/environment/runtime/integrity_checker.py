"""
Integrity checker module — verifies HMAC-SHA256 signatures on allocation
request payloads to detect tampering or corruption.
"""

import hmac
import hashlib
import base64


def verify_request_integrity(request, key_str, key_encoding):
    """
    Verify the HMAC-SHA256 signature of a request's payload.

    Args:
        request: dict with 'payload' and 'signature' fields
        key_str: the signing key string from config
        key_encoding: encoding type ('base64' or 'raw')

    Returns:
        True if signature is valid, False otherwise
    """
    payload = request.get("payload", "")
    expected_sig = request.get("signature", "")

    signing_key = key_str.encode("utf-8")

    computed = hmac.new(signing_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected_sig)


def check_all_integrity(requests, config):
    """
    Check integrity of all requests using configured signing key.
    Returns requests annotated with 'integrity_valid' field.
    """
    key_str = config.get("ledger", "integrity_key")
    key_encoding = config.get("ledger", "key_encoding")

    checked = []
    for req in requests:
        result = dict(req)
        result["integrity_valid"] = verify_request_integrity(req, key_str, key_encoding)
        checked.append(result)

    return checked
