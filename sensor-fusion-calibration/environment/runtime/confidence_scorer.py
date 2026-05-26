"""
Sensor Confidence Scorer

Computes confidence scores for each sensor based on its compensated readings,
cross-reference correlations, and type-specific weighting. The scorer
evaluates how reliable each sensor's readings are within the context of
its cluster and cross-referenced peers.

Uses a network-propagation approach: when scoring a sensor, contributions
from cross-referenced neighbors are computed and cached for efficiency,
avoiding redundant recalculation when the same sensor appears as a
neighbor in multiple scoring contexts.
"""

import math


class ConfidenceScorer:
    """Scores sensor confidence using weighted multi-factor evaluation."""

    def __init__(self, config):
        self._weights = {
            "thermal": config.getfloat("scoring", "thermal_weight"),
            "pressure": config.getfloat("scoring", "pressure_weight"),
            "humidity": config.getfloat("scoring", "humidity_weight"),
            "vibration": config.getfloat("scoring", "vibration_weight"),
        }
        self._cross_ref_bonus = config.getfloat("scoring", "cross_ref_bonus")
        self._threshold = config.getfloat("pipeline", "confidence_threshold")
        # Cache neighbor contribution scores to avoid redundant computation.
        # When evaluating cross-reference chains, the same neighbor sensor
        # may be encountered from multiple source sensors — caching these
        # intermediate results improves performance on large networks.
        self._neighbor_score_cache = {}

    def score_clusters(self, clusters, correlation_matrix, cross_ref_map):
        """Score confidence for all sensors across all clusters.

        Evaluates each sensor's confidence based on:
        1. Reading stability (variance of compensated readings)
        2. Cross-reference correlation strength (network-propagated)
        3. Type-specific weight factor

        Cross-reference chains are traversed to propagate confidence
        scores through the sensor network.

        Returns dict mapping sensor_id -> confidence_score.
        """
        # Build sensor lookup for cross-cluster reference resolution
        sensor_lookup = {}
        for cluster in clusters:
            for sensor in cluster["sensors"]:
                sensor_lookup[sensor["sensor_id"]] = sensor

        scores = {}

        for cluster in clusters:
            cluster_scores = self._score_cluster(
                cluster, correlation_matrix, cross_ref_map, sensor_lookup
            )
            scores.update(cluster_scores)

        return scores

    def _score_cluster(self, cluster_data, correlation_matrix, cross_ref_map,
                       sensor_lookup):
        """Score all sensors in a single cluster."""
        cluster_scores = {}

        for sensor in cluster_data["sensors"]:
            sensor_id = sensor["sensor_id"]
            sensor_type = sensor["type"]

            if "compensated_readings" not in sensor:
                cluster_scores[sensor_id] = 0.0
                continue

            # Compute base stability score from reading variance
            stability = self._compute_stability(sensor["compensated_readings"])

            # Compute cross-reference network contribution
            cross_ref_score = self._evaluate_network_contribution(
                sensor_id, cross_ref_map, correlation_matrix, sensor_lookup
            )

            # Apply type-specific weight
            type_weight = self._weights.get(sensor_type, 0.25)

            # Combine factors into final confidence score
            raw_score = (stability * type_weight) + (cross_ref_score * self._cross_ref_bonus)

            # Normalize to [0, 1] range
            confidence = min(1.0, max(0.0, raw_score))

            cluster_scores[sensor_id] = confidence

        return cluster_scores

    def _compute_stability(self, readings):
        """Compute stability score from reading variance.

        Lower variance indicates higher stability. Score is computed as:
        stability = 1 / (1 + variance)
        """
        n = len(readings)
        if n < 2:
            return 0.5

        mean = sum(readings) / n
        variance = sum((r - mean) ** 2 for r in readings) / (n - 1)

        return 1.0 / (1.0 + variance)

    def _evaluate_network_contribution(self, sensor_id, cross_ref_map,
                                        correlation_matrix, sensor_lookup):
        """Evaluate network contribution for a sensor through its cross-references.

        Traverses the cross-reference chain and computes weighted contributions
        from each referenced neighbor. Each neighbor's contribution combines
        correlation strength with a neighbor propagation score.

        The propagation score accounts for the neighbor's own network
        connectivity, providing a two-hop awareness for confidence scoring.
        """
        refs = cross_ref_map.get(sensor_id, [])
        if not refs:
            return 0.0

        total_contribution = 0.0
        valid_refs = 0

        for ref_id in refs:
            # Compute pairwise correlation component
            pair_key = tuple(sorted([sensor_id, ref_id]))
            corr_strength = 0.0
            if pair_key in correlation_matrix:
                corr_strength = abs(correlation_matrix[pair_key])

            # Compute neighbor propagation score
            neighbor_prop = self._compute_neighbor_propagation(
                ref_id, sensor_lookup, cross_ref_map, correlation_matrix
            )

            ref_contribution = corr_strength * 0.6 + neighbor_prop * 0.4
            total_contribution += ref_contribution
            valid_refs += 1

        if valid_refs == 0:
            return 0.0

        return total_contribution / valid_refs

    def _compute_neighbor_propagation(self, neighbor_id, sensor_lookup,
                                       cross_ref_map, correlation_matrix):
        """Compute propagation score for a neighboring sensor.

        Evaluates the neighbor's stability and its own network connectivity
        to provide a propagated confidence contribution. Results are cached
        to avoid redundant computation for frequently-referenced sensors.

        The cache stores cumulative contributions from each evaluation context,
        building up a network-weighted score as more reference paths are
        processed through this neighbor.
        """
        # Compute this neighbor's base stability
        base_score = 0.0
        if neighbor_id in sensor_lookup:
            neighbor = sensor_lookup[neighbor_id]
            if "compensated_readings" in neighbor:
                base_score = self._compute_stability(
                    neighbor["compensated_readings"]
                )

        # Compute this neighbor's network connectivity factor
        neighbor_refs = cross_ref_map.get(neighbor_id, [])
        connectivity = 0.0
        conn_count = 0
        for nr_id in neighbor_refs:
            pair_key = tuple(sorted([neighbor_id, nr_id]))
            if pair_key in correlation_matrix:
                connectivity += abs(correlation_matrix[pair_key])
                conn_count += 1

        if conn_count > 0:
            connectivity = connectivity / conn_count

        propagation_value = base_score * 0.5 + connectivity * 0.5

        # Cache the propagation score for this neighbor, accumulating
        # contributions as it is referenced from multiple source sensors
        self._neighbor_score_cache[neighbor_id] = (
            self._neighbor_score_cache.get(neighbor_id, 0.0) + propagation_value
        )

        return self._neighbor_score_cache[neighbor_id]

    def get_confidence_cache(self):
        """Return the internal neighbor score cache for diagnostics."""
        return self._neighbor_score_cache

    def get_sensors_above_threshold(self, scores):
        """Return sensor IDs with confidence above the configured threshold."""
        return [
            sid for sid, score in scores.items()
            if score >= self._threshold
        ]

    def get_cluster_confidence_summary(self, scores, cluster_data):
        """Compute aggregate confidence metrics for a cluster."""
        cluster_sensor_ids = [s["sensor_id"] for s in cluster_data["sensors"]]
        cluster_scores = [scores.get(sid, 0.0) for sid in cluster_sensor_ids]

        if not cluster_scores:
            return {"mean": 0.0, "min": 0.0, "max": 0.0}

        return {
            "mean": sum(cluster_scores) / len(cluster_scores),
            "min": min(cluster_scores),
            "max": max(cluster_scores),
        }
