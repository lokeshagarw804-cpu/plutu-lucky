#!/usr/bin/env python3
"""Repair script for lattice consensus analyzer.

Patches four interacting defects across the loader, DAG builder,
weight calculator, and finality checker modules, then re-runs.
"""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from comma-separated validator list.

    The config has a trailing space before validator_4 in the
    active_validators value. Without strip(), ' validator_4' never
    matches 'validator_4' from the data files.
    """
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
    """Fix Bug B: read from consensus.finality section, not consensus.

    The consensus section has quorum_threshold=0.80 (a less strict value
    used for pre-confirmation). The consensus.finality section has the
    correct strict threshold of 0.67 and confirmation_depth of 2.
    """
    path = "/app/runtime/finality_checker.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._threshold = self._config.getfloat("consensus", "quorum_threshold")',
        'self._threshold = self._config.getfloat("consensus.finality", "quorum_threshold")'
    )
    content = content.replace(
        'self._depth = self._config.getint("consensus", "confirmation_depth")',
        'self._depth = self._config.getint("consensus.finality", "confirmation_depth")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_weight_calculator():
    """Fix Bug C: count each validator only at earliest confirming round.

    The buggy code adds a validator's stake in every round they appear
    (via transitive BFS), causing double-counting. The fix tracks which
    round each validator FIRST confirms and only counts stake there.
    """
    path = "/app/runtime/weight_calculator.py"
    with open(path, "r") as f:
        content = f.read()

    # Replace the _find_round_confirmations method to track earliest only
    old_method = '''    def _find_round_confirmations(self, tx_id, children, tx_lookup,
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

        return round_validators'''

    new_method = '''    def _find_round_confirmations(self, tx_id, children, tx_lookup,
                                  tx_round, validators):
        """Find distinct validators confirming a tx, grouped by round.

        Each validator is counted only in the earliest round where they
        first confirm the transaction, preventing stake double-counting.

        Returns dict mapping round_number -> set of validator_ids.
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

        # Rebuild round_validators from earliest assignments
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
    """Fix Bug D: add validator_id to sort key for deterministic ordering.

    When multiple validators issue transactions at the same timestamp,
    sorting by (timestamp, seq) alone is non-deterministic because seq
    is local to each validator. The correct key is
    (timestamp, validator_id, seq).
    """
    path = "/app/runtime/dag_builder.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'all_txs.sort(key=lambda t: (t["timestamp"], t["seq"]))',
        'all_txs.sort(key=lambda t: (t["timestamp"], t["validator_id"], t["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_finality_checker()
    patch_weight_calculator()
    patch_dag_builder()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_consensus import main as run_main
    run_main()


if __name__ == "__main__":
    main()
