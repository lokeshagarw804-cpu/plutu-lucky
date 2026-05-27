"""Collision statistics reporter.

Aggregates collision data and produces summary metrics from the
resolver's interaction history.
"""
import json
import os
from configparser import ConfigParser


class CollisionReporter:
    """Generate collision reports and summary statistics."""

    def __init__(self, config: ConfigParser):
        self._output_dir = config.get("grid", "output_dir")

    def write_reports(self, collisions: list[dict],
                      history: dict[str, list[dict]]) -> None:
        """Write collision details and summary statistics to output."""
        os.makedirs(self._output_dir, exist_ok=True)

        # Write detailed collision list
        collisions_path = os.path.join(self._output_dir, "collisions.json")
        output_collisions = []
        for c in collisions:
            output_collisions.append({
                "pair": c["pair"],
                "cell": c["cell"],
                "response_velocity": c["response_velocity"],
                "restitution": c["restitution"],
            })
        with open(collisions_path, "w") as f:
            json.dump(output_collisions, f, indent=2)

        # Compute summary statistics from history
        total_collisions = 0
        all_velocities = []
        cells_with_collisions = set()

        for pair_key, interactions in history.items():
            if isinstance(interactions, list):
                total_collisions += len(interactions)
                for entry in interactions:
                    all_velocities.append(entry["response_velocity"])
                    cells_with_collisions.add(tuple(entry["cell"]))
            else:
                # Single entry (not a list)
                total_collisions += 1
                all_velocities.append(interactions["response_velocity"])
                cells_with_collisions.add(tuple(interactions["cell"]))

        unique_pairs = len(history)
        avg_velocity = (sum(all_velocities) / len(all_velocities)
                        if all_velocities else 0.0)
        max_velocity = max(all_velocities) if all_velocities else 0.0

        summary = {
            "total_collisions": total_collisions,
            "unique_pairs": unique_pairs,
            "avg_response_velocity": round(avg_velocity, 6),
            "max_response_velocity": round(max_velocity, 6),
            "cells_with_collisions": len(cells_with_collisions),
        }

        summary_path = os.path.join(self._output_dir, "summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
