"""
Sensor Cluster Data Loader

Handles loading and initial parsing of sensor cluster JSON files.
Validates schema conformance and builds the sensor registry for
downstream pipeline stages.
"""

import json
import os
from configparser import ConfigParser


class ClusterLoader:
    """Loads sensor cluster data from JSON files in the configured data directory."""

    def __init__(self, data_dir, config_path):
        self._data_dir = data_dir
        self._config = ConfigParser()
        self._config.read(config_path)
        self._cluster_order = self._config.get("clusters", "order").split(",")
        self._registry = {}
        self._cross_ref_map = {}

    def load_all(self):
        """Load all cluster files in the configured order.

        Returns a list of cluster dictionaries with validated sensor data.
        Builds internal cross-reference map for downstream correlation.
        """
        clusters = []
        for cluster_name in self._cluster_order:
            file_path = os.path.join(self._data_dir, f"cluster_{cluster_name}.json")
            if not os.path.exists(file_path):
                raise FileNotFoundError(
                    f"Missing cluster data file: {file_path}"
                )
            with open(file_path, "r") as f:
                cluster_data = json.load(f)

            self._validate_cluster(cluster_data, cluster_name)
            self._register_sensors(cluster_data)
            clusters.append(cluster_data)

        return clusters

    def _validate_cluster(self, cluster_data, expected_name):
        """Validate cluster schema and naming consistency."""
        if cluster_data.get("cluster_id") != expected_name:
            raise ValueError(
                f"Cluster ID mismatch: expected '{expected_name}', "
                f"got '{cluster_data.get('cluster_id')}'"
            )
        if "sensors" not in cluster_data:
            raise ValueError(f"Cluster '{expected_name}' missing sensors array")

        for sensor in cluster_data["sensors"]:
            required_fields = ["sensor_id", "type", "readings", "baseline",
                             "drift_rate", "cross_refs"]
            for field in required_fields:
                if field not in sensor:
                    raise ValueError(
                        f"Sensor {sensor.get('sensor_id', 'UNKNOWN')} "
                        f"missing required field: {field}"
                    )
            if len(sensor["readings"]) < 5:
                raise ValueError(
                    f"Sensor {sensor['sensor_id']} has insufficient readings "
                    f"(minimum 5, got {len(sensor['readings'])})"
                )

    def _register_sensors(self, cluster_data):
        """Register sensors and build cross-reference map."""
        cluster_id = cluster_data["cluster_id"]
        for sensor in cluster_data["sensors"]:
            sensor_id = sensor["sensor_id"]
            self._registry[sensor_id] = {
                "cluster": cluster_id,
                "type": sensor["type"],
                "baseline": sensor["baseline"],
                "drift_rate": sensor["drift_rate"],
            }
            self._cross_ref_map[sensor_id] = sensor["cross_refs"]

    def get_registry(self):
        """Return the complete sensor registry."""
        return self._registry

    def get_cross_ref_map(self):
        """Return the cross-reference map for all sensors."""
        return self._cross_ref_map

    def get_sensor_count(self):
        """Return total number of registered sensors."""
        return len(self._registry)
