"""Trust scorer — assigns trust scores to tokens based on issuer chain distance."""

import configparser


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read("/app/runtime/config.ini")
    return config


def get_issuer_distance(issuer, config=None):
    """Determine the chain distance from the root issuer.

    The root issuer has distance 0, each hop away adds 1.
    Known issuers:
      auth-primary (root) -> distance 0
      auth-backup -> distance 1
      auth-legacy -> distance 2
    Unknown issuers -> distance 3
    """
    if config is None:
        config = load_config()

    root_issuer = config.get("scoring", "root_issuer")

    issuer_chain = {
        root_issuer: 0,
        "auth-backup": 1,
        "auth-legacy": 2
    }

    return issuer_chain.get(issuer, 3)


def compute_trust_score(token, config=None):
    """Compute the trust score for a token based on its issuer chain distance.

    Formula: base_score * (decay_factor ** distance)
    Where distance is the hop count from root issuer.
    """
    if config is None:
        config = load_config()

    base_score = float(config.get("scoring", "base_score"))
    decay_factor = float(config.get("scoring", "decay_factor"))
    issuer = token["issuer"]

    distance = get_issuer_distance(issuer, config)
    score = base_score * (decay_factor ** (distance + 1))

    return round(score, 4)


def score_batch(tokens, config=None):
    """Score all tokens in a batch.

    Returns list of (token, score) tuples.
    """
    results = []
    for token in tokens:
        score = compute_trust_score(token, config)
        results.append((token, score))
    return results
