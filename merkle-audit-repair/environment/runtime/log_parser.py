"""Transaction log parser for Merkle audit system.

Reads ledger files from the data directory and assembles them into
an ordered sequence of transactions for tree construction.
"""
import json
import os


DATA_DIR = "/app/runtime/data"


def load_transactions():
    """Load all transactions from ledger files in sorted order.

    Reads all ledger_*.json files from the data directory and concatenates
    their transaction arrays in filename-sorted order to produce a
    deterministic global transaction sequence.

    Returns:
        List of transaction dicts in canonical ledger order.
    """
    transactions = []
    ledger_files = sorted(
        f for f in os.listdir(DATA_DIR) if f.startswith("ledger_") and f.endswith(".json")
    )

    for filename in ledger_files:
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r") as fh:
            entries = json.load(fh)
            transactions.extend(entries)

    return transactions
