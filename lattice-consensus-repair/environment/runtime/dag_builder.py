"""DAG builder — constructs the transaction lattice from validator logs.

Merges transactions from all validators into a unified directed acyclic
graph. Each transaction references parent transactions forming the lattice.
Transactions are ordered by causal timestamp for consistent traversal.
"""


class DagBuilder:
    """Builds unified DAG from multiple validator transaction logs."""

    def build_lattice(self, validators):
        """Merge all validator transactions into a single DAG structure.

        Transactions from different validators are combined and sorted
        by timestamp for deterministic processing order. The DAG preserves
        parent-child relationships across validator boundaries.

        Returns a tuple of (sorted_transactions, children_map, tx_lookup).
        """
        all_txs = []
        tx_lookup = {}

        for vid, vdata in validators.items():
            for tx in vdata["transactions"]:
                node = {
                    "tx_id": tx["tx_id"],
                    "validator_id": vid,
                    "timestamp": tx["timestamp"],
                    "seq": tx["seq"],
                    "parents": tx["parents"],
                    "round": tx["round"],
                    "weight": tx["weight"],
                }
                all_txs.append(node)
                tx_lookup[tx["tx_id"]] = node

        # Sort transactions into causal processing order
        all_txs.sort(key=lambda t: (t["timestamp"], t["seq"]))

        # Build parent -> children adjacency mapping
        children = {tx["tx_id"]: [] for tx in all_txs}
        for tx in all_txs:
            for parent_id in tx["parents"]:
                if parent_id in children:
                    children[parent_id].append(tx["tx_id"])

        return all_txs, children, tx_lookup
