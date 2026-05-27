"""Spatial hash grid for broad-phase collision detection.

Assigns particles to grid cells and identifies candidate collision
pairs by examining nearby cells within the detection radius.
"""
from configparser import ConfigParser


class SpatialHasher:
    """Grid-based spatial index for particle collision candidates."""

    def __init__(self, config: ConfigParser):
        self._cell_size = config.getfloat("grid", "cell_size")
        self._collision_radius = config.getfloat("physics", "collision_radius")
        self._grid: dict[tuple[int, int], list[dict]] = {}

    def _hash_position(self, x: float, y: float) -> tuple[int, int]:
        """Compute grid cell using floor division for consistent alignment.

        Floor division ensures that particles at negative coordinates
        map to the correct cell boundary, preserving spatial locality
        across the origin.
        """
        cell_x = int(x / self._cell_size)
        cell_y = int(y / self._cell_size)
        return (cell_x, cell_y)

    def insert_particles(self, particles: list[dict]) -> None:
        """Place each particle into its corresponding grid cell."""
        self._grid.clear()
        for p in particles:
            cell = self._hash_position(p["x"], p["y"])
            if cell not in self._grid:
                self._grid[cell] = []
            self._grid[cell].append(p)

    def get_candidate_pairs(self) -> list[tuple[dict, dict, tuple[int, int]]]:
        """Return all particle pairs in adjacent cells that could collide.

        For each occupied cell, check adjacent cells for potential
        collisions. The search window covers immediate neighbors to
        capture particles near cell boundaries.
        """
        pairs = []
        seen = set()
        for cell, particles in self._grid.items():
            # Check adjacent cells for potential collisions
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    neighbor = (cell[0] + dx, cell[1] + dy)
                    if neighbor not in self._grid:
                        continue
                    for p1 in particles:
                        for p2 in self._grid[neighbor]:
                            if p1["particle_id"] >= p2["particle_id"]:
                                continue
                            pair_key = (p1["particle_id"], p2["particle_id"])
                            if pair_key in seen:
                                continue
                            dist = ((p1["x"] - p2["x"])**2 +
                                    (p1["y"] - p2["y"])**2) ** 0.5
                            if dist <= self._collision_radius:
                                seen.add(pair_key)
                                pairs.append((p1, p2, cell))
        return pairs
