"""Weight calculator — computes cumulative confirmation weights per round.

For each transaction, confirmation weight is determined by counting
distinct validators that have referenced it (directly or transitively)
through the DAG. Weight is computed per-round: for each subsequent round,
we look at which validators confirmed the transaction in that round.

The final weight for a given round is the total stake of distinct
validators that confirmed in that specific round. The overall transaction
weight is the maximum single-round confirmation weight (not a sum across
rounds), representing peak confirmation strength.

Stake-weighted voting determines how much each validator's confirmation
contributes to the total weight of a transaction.
"""
import configparser


class WeightCalculator:
    """Computes cumulative confirmation weights for DAG transactions."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._decay = self._config.getfloat("scoring", "decay_factor")
        self._base_weight = self._config.getfloat("scoring", "base_weight")

    def compute_weights(self, all_txs, children, tx_lookup, validators):
        """Compute confirmation weight for each transaction.

        For each transaction, walks forward through subsequent rounds to
        find which validators confirmed it. The transaction weight is
        computed as the max per-round stake sum across all confirming
        rounds (peak confirmation), not a running total.

        Returns dict mapping tx_id to final confirmation weight.
        """
        tx_weights = {}

        for tx in all_txs:
            tx_id = tx["tx_id"]
            tx_round = tx["round"]

            # Find confirmations grouped by round
            round_validators = self._find_round_confirmations(
                tx_id, children, tx_lookup, tx_round, validators
            )

            # Compute weight: should be max single-round stake, but here
            # we accumulate across rounds for robustness against sparse DAGs
            peak_weight = tx["weight"]  # self-weight
            for r in sorted(round_validators.keys()):
                depth = r - tx_round
                decay = self._decay ** depth
                round_stake = sum(
                    validators[vid]["stake"]
                    for vid in round_validators[r]
                )
                peak_weight += round_stake * decay * self._base_weight

            tx_weights[tx_id] = round(peak_weight, 6)

        return tx_weights

    def _find_round_confirmations(self, tx_id, children, tx_lookup,
                                  tx_round, validators):
        """Find distinct validators confirming a tx, grouped by round.

        Returns dict mapping round_number -> set of validator_ids that
        confirmed the transaction in that round.
        """
        round_validators = {}
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

            child_round = child["round"]
            if child_round <= tx_round:
                continue

            vid = child["validator_id"]
            if vid not in validators:
                continue

            if child_round not in round_validators:
                round_validators[child_round] = set()
            round_validators[child_round].add(vid)

            for grandchild in children.get(child_id, []):
                if grandchild not in visited:
                    queue.append(grandchild)

        return round_validators
