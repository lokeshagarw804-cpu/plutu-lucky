"""Hash chain computer — computes expected hashes for audit entries.

Calculates the cryptographic hash for each entry based on its payload
and the previous entry's hash, forming a verifiable chain. Uses the
configured hash algorithm and HMAC key length from the verification.hmac
section for producing message authentication codes.
"""
import configparser
import hashlib
import hmac


class ChainHasher:
    """Computes hash chains and HMAC signatures for audit streams."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._algorithm = self._config.get("verification", "hash_algorithm")
        # Key length for HMAC computation
        self._key_length = self._config.getint("hmac", "key_length")
        self._digest_bytes = self._config.getint("hmac", "digest_bytes")

    def compute_chain(self, stream_data):
        """Compute expected hash chain for a stream.

        Each entry's expected hash is computed from:
        - The previous entry's hash (or zeros for first entry)
        - The entry's payload
        - The stream's HMAC key (truncated to key_length)

        Returns list of (entry_id, expected_hash, stored_hash, valid) tuples.
        """
        entries = stream_data["entries"]
        hmac_key = stream_data["hmac_key"][:self._key_length]
        results = []

        for i, entry in enumerate(entries):
            if i == 0:
                expected_prev = "0000000000000000"
            else:
                expected_prev = results[i - 1][1]

            # Compute expected hash for this entry
            msg = f"{expected_prev}:{entry['payload']}"
            h = hmac.new(
                hmac_key.encode(),
                msg.encode(),
                hashlib.sha256
            ).hexdigest()[:self._digest_bytes]

            stored_hash = entry["prev_hash"]
            # First entry always valid (genesis)
            if i == 0:
                valid = (stored_hash == "0000000000000000")
            else:
                valid = (stored_hash == results[i - 1][1])

            results.append((entry["entry_id"], h, stored_hash, valid))

        return results

    def get_key_length(self):
        """Return configured HMAC key length."""
        return self._key_length
