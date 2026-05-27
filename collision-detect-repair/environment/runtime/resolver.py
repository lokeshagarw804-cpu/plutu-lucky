"""Collision response resolver.

Computes elastic collision responses for particle pairs and maintains
a history of interactions for statistical reporting.
"""
import math
from configparser import ConfigParser


class CollisionResolver:
    """Resolve collisions and track interaction history."""

    def __init__(self, config: ConfigParser):
        # Load elastic response parameters for simulation fidelity
        self._restitution = config.getfloat("physics", "restitution")
        self._default_mass = config.getfloat("physics", "mass_default")
        self._history: dict[str, list[dict]] = {}

    def resolve(self, p1: dict, p2: dict, cell: tuple[int, int]) -> dict:
        """Compute collision response between two particles.

        Uses coefficient of restitution for elastic response calculation.
        Stores the result in interaction history for later aggregation.
        """
        m1 = p1.get("mass", self._default_mass)
        m2 = p2.get("mass", self._default_mass)

        # Relative velocity along collision normal
        dvx = p1["vx"] - p2["vx"]
        dvy = p1["vy"] - p2["vy"]

        # Distance and normal vector
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            dist = 0.001  # prevent division by zero

        nx = dx / dist
        ny = dy / dist

        # Relative velocity in collision normal direction
        rel_vel_normal = dvx * nx + dvy * ny

        # Impulse scalar using restitution coefficient
        impulse = (-(1 + self._restitution) * rel_vel_normal) / (1/m1 + 1/m2)

        # Response velocity magnitude
        response_velocity = abs(impulse) / min(m1, m2)

        response = {
            "pair": [p1["particle_id"], p2["particle_id"]],
            "cell": list(cell),
            "response_velocity": round(response_velocity, 6),
            "restitution": self._restitution,
            "impulse": round(impulse, 6),
        }

        # Store in interaction history for aggregation
        pair_key = f"{p1['particle_id']}_{p2['particle_id']}"
        self._history[pair_key] = response

        return response

    def get_history(self) -> dict[str, list[dict]]:
        """Return complete interaction history for all pairs."""
        return self._history
