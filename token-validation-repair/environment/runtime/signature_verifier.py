"""Signature verifier — validates HMAC-SHA256 signatures on tokens."""

import hmac
import hashlib
import configparser


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read("/app/runtime/config.ini")
    return config


def get_signing_key(config=None):
    """Retrieve the signing key from configuration."""
    if config is None:
        config = load_config()

    key_str = config.get("tokens", "signing_key")
    return key_str.encode("utf-8")


def verify_signature(token, config=None):
    """Verify the HMAC-SHA256 signature of a token.

    Args:
        token: dict with 'payload' (JSON string) and 'signature' (hex string)
        config: optional config object

    Returns:
        bool indicating whether the signature is valid
    """
    key = get_signing_key(config)
    payload_bytes = token["payload"].encode("utf-8")
    expected_sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, token["signature"])


def verify_batch(tokens, config=None):
    """Verify signatures for a batch of tokens.

    Returns:
        list of (token, is_valid) tuples
    """
    results = []
    for token in tokens:
        valid = verify_signature(token, config)
        results.append((token, valid))
    return results
