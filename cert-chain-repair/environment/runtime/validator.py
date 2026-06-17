"""
Trust store validator.

Determines whether a certificate is issued by a trusted root CA
based on the configured trust store. Also enforces minimum key
strength and allowed signature algorithms.
"""

import configparser


class TrustValidator:
    """Validates certificates against the trust store configuration."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        raw_roots = config.get("trust_store", "trusted_roots")
        self._trusted_roots = set(raw_roots.split(","))
        self._min_key_bits = config.getint("trust_store", "min_key_bits")
        self._allowed_algos = set(
            config.get("trust_store", "allowed_algorithms").split(",")
        )

    def is_trusted_issuer(self, issuer_id):
        """Check if the issuer is in the trusted roots set."""
        return issuer_id in self._trusted_roots

    def validate_key_strength(self, key_bits):
        """Check if key meets minimum bit length."""
        return key_bits >= self._min_key_bits

    def validate_algorithm(self, algo):
        """Check if signature algorithm is allowed."""
        return algo in self._allowed_algos

    def validate_certificate(self, cert):
        """Full validation of a single certificate.

        Returns a dict with validation results.
        """
        trusted = self.is_trusted_issuer(cert["issuer_id"])
        strong_key = self.validate_key_strength(cert["key_bits"])
        valid_algo = self.validate_algorithm(cert["signature_algo"])

        return {
            "cert_id": cert["cert_id"],
            "subject": cert["subject"],
            "issuer_id": cert["issuer_id"],
            "trusted_issuer": trusted,
            "strong_key": strong_key,
            "valid_algorithm": valid_algo,
            "fully_valid": trusted and strong_key and valid_algo,
        }
