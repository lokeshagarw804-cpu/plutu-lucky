"""
Package registry loader.

Reads package definitions from registry JSON files in /app/runtime/data/.
Each registry file contains packages with version info, scope, and
dependency constraints.
"""

import json
import os


def load_registry(data_dir="/app/runtime/data"):
    """Load all package records from registry files.

    Returns a list of package dicts from all registry sources.
    """
    packages = []
    for filename in sorted(os.listdir(data_dir)):
        if filename.startswith("registry_") and filename.endswith(".json"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                records = json.load(f)
                packages.extend(records)
    return packages
