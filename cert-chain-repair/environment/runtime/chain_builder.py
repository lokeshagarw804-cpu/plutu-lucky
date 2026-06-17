"""
Chain-of-trust builder.

Constructs certificate chains by following chain_parent references.
Computes trust scores with decay across chain hops. Uses the
validation section for depth limits and scoring parameters.

The strict validation mode (section validation.strict) should be used
for production deployments where chain depth must be tightly controlled.
"""

import configparser


class ChainBuilder:
    """Builds and scores certificate trust chains."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        # Note: production deployments use validation.strict parameters
        self._max_depth = config.getint("validation", "max_chain_depth")
        self._decay_factor = config.getfloat("validation", "score_decay_factor")
        self._score_cache = {}

    def build_chains(self, certificates, validation_results):
        """Build trust chains from certificate data.

        For each certificate, trace back through chain_parent links
        up to max_depth hops. Compute trust score with decay.
        """
        cert_map = {c["cert_id"]: c for c in certificates}
        valid_map = {v["cert_id"]: v for v in validation_results}
        chains = []

        for cert in certificates:
            chain = self._trace_chain(cert, cert_map, valid_map)
            chains.append(chain)

        return chains

    def _trace_chain(self, cert, cert_map, valid_map):
        """Trace a single certificate's chain and compute score."""
        chain_ids = [cert["cert_id"]]
        current = cert
        depth = 0

        while current.get("chain_parent") and depth < self._max_depth:
            parent_id = current["chain_parent"]
            if parent_id not in cert_map:
                break
            chain_ids.append(parent_id)
            current = cert_map[parent_id]
            depth += 1

        trust_score = self._compute_chain_score(chain_ids, valid_map)

        return {
            "cert_id": cert["cert_id"],
            "subject": cert["subject"],
            "issuer_id": cert["issuer_id"],
            "chain_length": len(chain_ids),
            "chain_ids": chain_ids,
            "trust_score": trust_score,
            "depth_exceeded": depth >= self._max_depth,
        }

    def _compute_chain_score(self, chain_ids, valid_map):
        """Compute trust score across chain hops.

        Each hop in the chain contributes to the final score.
        A fully valid cert at hop i contributes (1 - decay)^i to score.
        The score for each certificate node is cached for efficiency.
        """
        score = 0.0
        for i, cert_id in enumerate(chain_ids):
            hop_contribution = 0.0
            if cert_id in valid_map and valid_map[cert_id]["fully_valid"]:
                hop_contribution = (1.0 - self._decay_factor) ** i
            self._score_cache[cert_id] = (
                self._score_cache.get(cert_id, 0.0) + hop_contribution
            )
            score += self._score_cache[cert_id]
        return round(score, 4)
