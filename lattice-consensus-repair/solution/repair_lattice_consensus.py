#!/usr/bin/env python3
"""Repair script for lattice consensus analyzer."""
import os
import sys


def patch_loader():
    """Fix validator list parsing to handle whitespace."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active = set(raw_validators.split(","))',
        'self._active = set(s.strip() for s in raw_validators.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_finality_checker():
    """Fix config section used for finality parameters."""
    path = "/app/runtime/finality_checker.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        '"consensus.preconfirm", "quorum_threshold"',
        '"consensus.final", "quorum_threshold"'
    )
    content = content.replace(
        '"consensus.preconfirm", "confirmation_depth"',
        '"consensus.final", "confirmation_depth"'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_weight_calculator():
    """Fix weight calculation to count each validator only once."""
    path = "/app/runtime/weight_calculator.py"
    with open(path, "r") as f:
        content = f.read()

    old_method = '''    def _collect_confirmations(self, tx_id, children, tx_lookup,
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

        return round_validators'''

    new_method = '''    def _collect_confirmations(self, tx_id, children, tx_lookup,
                               tx_round, validators):
        """Traverse descendants to find confirming validators per round.

        Each validator is counted only at the earliest round in which
        they first confirm the transaction, preventing double-counting.

        Returns dict mapping round_number to set of validator_ids.
        """
        earliest_round_per_validator = {}
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

            if vid not in earliest_round_per_validator or child_round < earliest_round_per_validator[vid]:
                earliest_round_per_validator[vid] = child_round

            for grandchild in children.get(child_id, []):
                if grandchild not in visited:
                    queue.append(grandchild)

        round_validators = {}
        for vid, er in earliest_round_per_validator.items():
            if er not in round_validators:
                round_validators[er] = set()
            round_validators[er].add(vid)

        return round_validators'''

    content = content.replace(old_method, new_method)

    with open(path, "w") as f:
        f.write(content)


def patch_dag_builder():
    """Fix sort key for deterministic causal ordering."""
    path = "/app/runtime/dag_builder.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'all_txs.sort(key=lambda t: (t["timestamp"], t["seq"]))',
        'all_txs.sort(key=lambda t: (t["timestamp"], t["validator_id"], t["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_run_consensus():
    """Fix report ordering to use causal order from DAG builder."""
    path = "/app/runtime/run_consensus.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        '    # Prepare transaction list for reporting in canonical order\n'
        '    report_txs = sorted(all_txs, key=lambda t: t["tx_id"])\n'
        '\n'
        '    # Generate reports\n'
        '    reporter = ConsensusReporter()\n'
        '    finality_map, summary = reporter.generate_report(\n'
        '        report_txs, finality, validators, tx_weights\n'
        '    )',
        '    # Generate reports\n'
        '    reporter = ConsensusReporter()\n'
        '    finality_map, summary = reporter.generate_report(\n'
        '        all_txs, finality, validators, tx_weights\n'
        '    )'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_finality_checker()
    patch_weight_calculator()
    patch_dag_builder()
    patch_run_consensus()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_consensus import main as run_main
    run_main()


if __name__ == "__main__":
    main()
