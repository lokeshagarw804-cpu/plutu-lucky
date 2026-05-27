"""Finality checker — determines which transactions have reached finality.

A transaction achieves finality when its cumulative confirmation weight
from distinct validators exceeds the configured quorum threshold and
has been confirmed to sufficient depth in the DAG.
"""
import configparser


class FinalityChecker:
    """Checks transaction finality against quorum parameters."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat(
            "consensus.preconfirm", "quorum_threshold"
        )
        self._depth = self._config.getint(
            "consensus.preconfirm", "confirmation_depth"
        )

    def check_finality(self, all_txs, tx_weights, children, tx_lookup,
                       validators):
        """Determine finality status for each transaction.

        A transaction is final if:
        1. Its normalized confirmation weight exceeds quorum_threshold
        2. It has been confirmed at least confirmation_depth rounds deep

        Returns dict mapping tx_id to finality status dict.
        """
        finality = {}
        total_stake = sum(v["stake"] for v in validators.values())

        for tx in all_txs:
            tx_id = tx["tx_id"]
            weight = tx_weights.get(tx_id, 0.0)
            tx_round = tx["round"]

            max_desc_round = self._max_descendant_round(
                tx_id, children, tx_lookup
            )
            depth_reached = max_desc_round - tx_round

            normalized_weight = weight / total_stake if total_stake > 0 else 0.0

            is_final = (
                normalized_weight >= self._threshold
                and depth_reached >= self._depth
            )

            finality[tx_id] = {
                "tx_id": tx_id,
                "validator_id": tx["validator_id"],
                "round": tx_round,
                "weight": weight,
                "normalized_weight": round(normalized_weight, 6),
                "depth_reached": depth_reached,
                "is_final": is_final,
            }

        return finality

    def _max_descendant_round(self, tx_id, children, tx_lookup):
        """Find the maximum round reached by any descendant."""
        max_round = tx_lookup[tx_id]["round"]
        visited = set()
        queue = list(children.get(tx_id, []))

        while queue:
            child_id = queue.pop(0)
            if child_id in visited:
                continue
            visited.add(child_id)

            child = tx_lookup.get(child_id)
            if child is None:
                continue
            if child["round"] > max_round:
                max_round = child["round"]

            for gc in children.get(child_id, []):
                if gc not in visited:
                    queue.append(gc)

        return max_round
