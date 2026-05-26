"""Policy checker — validates tokens against expiry, issuer trust, and scope rules."""

import json
import configparser

REFERENCE_TIME = 1700000000


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read("/app/runtime/config.ini")
    return config


def check_expiry(token, config=None):
    """Check whether a token has expired within the allowed clock drift.

    Uses the max_clock_drift_sec from policy configuration to determine
    if a token is still within acceptable bounds.
    """
    if config is None:
        config = load_config()

    max_drift = int(config.get("policy", "max_clock_drift_sec"))
    expires_at = token["expires_at"]

    if expires_at >= REFERENCE_TIME:
        return True

    elapsed = REFERENCE_TIME - expires_at
    return elapsed <= max_drift


def check_issuer(token, config=None):
    """Check whether the token issuer is in the allowed list."""
    if config is None:
        config = load_config()

    allowed = config.get("policy", "allowed_issuers").split(",")
    return token["issuer"] in allowed


def check_scopes(token, config=None):
    """Check whether the token has sufficient scope permissions."""
    if config is None:
        config = load_config()

    min_match = int(config.get("policy", "min_scope_match"))
    required_scopes = ["read:data", "write:data", "admin:config", "read:logs", "write:logs"]
    token_scopes = token["scopes"]

    matches = len(set(token_scopes) & set(required_scopes))
    return matches >= min_match


def validate_token(token, config=None):
    """Run all policy checks on a token.

    Returns:
        dict with check results: expired, issuer_valid, scopes_valid, policy_pass
    """
    expired = not check_expiry(token, config)
    issuer_valid = check_issuer(token, config)
    scopes_valid = check_scopes(token, config)

    policy_pass = (not expired) and issuer_valid and scopes_valid

    return {
        "token_id": token["token_id"],
        "expired": expired,
        "issuer_valid": issuer_valid,
        "scopes_valid": scopes_valid,
        "policy_pass": policy_pass
    }
