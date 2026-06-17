"""Validator log loader — reads transaction DAG data from JSON files.

Each validator produces a log of transactions with parent references
forming a DAG structure. The loader reads active validators from
configuration and returns their transaction sets.
"""
import configparser
import json
import os


class ValidatorLoader:
    """Loads transaction DAG data from validator log files."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("network", "source_dir")
        raw_validators = self._config.get("validators", "active_validators")
        self._active = set(raw_validators.split(","))

    def load_validators(self):
        """Load transaction logs for all active validators.

        Returns dict mapping validator_id to their full transaction data.
        Only validators listed in active_validators config are loaded.
        """
        validators = {}
        data_dir = self._source_dir

        for fname in sorted(os.listdir(data_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(data_dir, fname)
            with open(path, "r") as f:
                data = json.load(f)

            vid = data["validator_id"]
            if vid not in self._active:
                continue

            validators[vid] = {
                "validator_id": vid,
                "stake": data["stake"],
                "start_round": data["start_round"],
                "transactions": data["transactions"],
            }

        return validators
