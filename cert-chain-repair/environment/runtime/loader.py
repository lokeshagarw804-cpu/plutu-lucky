"""
Certificate data loader.

Reads certificate records from authority JSON files in /app/runtime/data/.
Each authority file represents a distinct issuing CA with its own cert inventory.
"""

import json
import os


def load_certificates(data_dir="/app/runtime/data"):
    """Load all certificate records from authority data files.

    Returns a list of certificate dicts sorted by issued_date.
    """
    certificates = []
    for filename in sorted(os.listdir(data_dir)):
        if filename.startswith("authority_") and filename.endswith(".json"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                records = json.load(f)
                certificates.extend(records)
    certificates.sort(key=lambda c: c["issued_date"])
    return certificates
