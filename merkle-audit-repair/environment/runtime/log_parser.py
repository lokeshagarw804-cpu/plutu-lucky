"""Log parser — reads transaction entries from ledger files.

Each ledger file contains a JSON array of transactions. Entries
are loaded, validated, and normalized into a canonical format
for downstream hashing and tree construction.
"""
import json
import os


class LogParser:
    """Parses and normalizes transaction log entries."""

    def __init__(self, data_dir):
        self._data_dir = data_dir

    def parse_ledgers(self):
        """Load all ledger files and return flat list of transactions.

        Each transaction dict has: txn_id, timestamp, account,
        txn_type, amount. Transactions are returned in ledger file
        order (alphabetical by filename), then entry order within file.
        """
        transactions = []
        for filename in sorted(os.listdir(self._data_dir)):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self._data_dir, filename)
            with open(filepath, "r") as f:
                ledger = json.load(f)
            for entry in ledger["transactions"]:
                txn = {
                    "txn_id": entry["txn_id"],
                    "timestamp": str(entry["timestamp"]),
                    "account": entry["account"],
                    "txn_type": entry["txn_type"],
                    "amount": str(entry["amount"]),
                }
                transactions.append(txn)
        return transactions
