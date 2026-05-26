"""Cluster builder — groups nearby points into spatial clusters.

Uses distance-based clustering with a configured threshold. Points
within distance_threshold of a cluster centroid are assigned to that
cluster. When multiple points have the same timestamp, they must be
ordered by layer_id alphabetically then seq within that layer for
deterministic cluster assignment.

Note: seq is local to each layer — it does not provide global ordering.
"""
import configparser
import math


class ClusterBuilder:
    """Groups spatial points into distance-based clusters."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._min_points = self._config.getint("clustering", "min_points")
        self._threshold = self._config.getfloat(
            "clustering", "distance_threshold"
        )

    def build_clusters(self, all_points):
        """Group points into clusters using distance threshold.

        Points are processed in order. Each point is assigned to the
        nearest existing cluster if within threshold, otherwise starts
        a new cluster. Only clusters with >= min_points are retained.

        Returns list of cluster dicts with members and centroids.
        """
        clusters = []

        for point in all_points:
            assigned = False
            best_dist = float("inf")
            best_cluster_idx = -1

            for idx, cluster in enumerate(clusters):
                cx = cluster["centroid_x"]
                cy = cluster["centroid_y"]
                dist = math.sqrt(
                    (point["x"] - cx) ** 2 + (point["y"] - cy) ** 2
                )
                if dist <= self._threshold and dist < best_dist:
                    best_dist = dist
                    best_cluster_idx = idx
                    assigned = True

            if assigned:
                cluster = clusters[best_cluster_idx]
                cluster["members"].append(point["point_id"])
                # Update centroid (running average)
                n = len(cluster["members"])
                cluster["centroid_x"] = (
                    cluster["centroid_x"] * (n - 1) + point["x"]
                ) / n
                cluster["centroid_y"] = (
                    cluster["centroid_y"] * (n - 1) + point["y"]
                ) / n
            else:
                clusters.append({
                    "cluster_id": len(clusters),
                    "centroid_x": point["x"],
                    "centroid_y": point["y"],
                    "members": [point["point_id"]],
                })

        # Filter by min_points
        valid_clusters = [
            c for c in clusters if len(c["members"]) >= self._min_points
        ]

        # Renumber and finalize
        for idx, c in enumerate(valid_clusters):
            c["cluster_id"] = idx
            c["member_count"] = len(c["members"])
            c["centroid_x"] = round(c["centroid_x"], 4)
            c["centroid_y"] = round(c["centroid_y"], 4)

        return valid_clusters

    def get_threshold(self):
        """Return distance threshold."""
        return self._threshold
