"""Weight calculator — computes confirmation weights for DAG transactions.

Confirmation weight measures how strongly a transaction has been endorsed
by the validator set. Weight is derived from stake-weighted confirmations
observed through the DAG's descendant graph.
"""
import configparser


class WeightCalculator:
    """Computes stake-weighted confirmation weights for transactions."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._decay = self._config.getfloat("scoring", "decay_factor")
        self._base_weight = self._config.getfloat("scoring", "base_weight")

    def compute_weights(self, all_txs, children, tx_lookup, validators):
        """Compute confirmation weight for each transaction.

        Walks forward through the DAG from each transaction to identify
        which validators have confirmed it. Confirmation weight is the
        sum of stake-weighted contributions from confirming validators,
        with a depth-based decay factor applied per round of distance.

        Returns dict mapping tx_id to computed weight.
        """
        tx_weights = {}

        for tx in all_txs:
            tx_id = tx["tx_id"]
            tx_round = tx["round"]

            round_validators = self._collect_confirmations(
                tx_id, children, tx_lookup, tx_round, validators
            )

            weight = tx["weight"]
            for r in sorted(round_validators.keys()):
                depth = r - tx_round
                decay = self._decay ** depth
                round_stake = sum(
                    validators[vid]["stake"]
                    for vid in round_validators[r]
                )
                weight += round_stake * decay * self._base_weight

            tx_weights[tx_id] = round(weight, 6)

        return tx_weights

    def _collect_confirmations(self, tx_id, children, tx_lookup,
                               tx_round, validators):
        """Traverse descendants to find confirming validators per round.

        Returns dict mapping round_number to set of validator_ids that
        confirmed the transaction in that round via the DAG.
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
