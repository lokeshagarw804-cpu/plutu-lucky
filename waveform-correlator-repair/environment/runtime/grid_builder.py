"""Coherence grid builder — assembles pairwise coherence into a matrix.

Builds a symmetric coherence grid from all receiver pair results,
computing the mean coherence across all windows for each pair.
The grid layout follows alphabetical receiver ordering.
"""
from itertools import combinations


class GridBuilder:
    """Assembles the receiver-pair coherence grid."""

    def build_grid(self, traces, pair_coherences):
        """Construct coherence grid from pairwise window results.

        Receivers are sorted by identifier for consistent grid layout.
        Returns dict with receiver_order, grid values, and dimensions.
        """
        receiver_ids = sorted(traces.keys())
        n = len(receiver_ids)

        # Initialize grid with zeros
        grid = [[0.0] * n for _ in range(n)]

        # Diagonal is always 1.0 (perfect self-coherence)
        for i in range(n):
            grid[i][i] = 1.0

        # Fill from pairwise results
        for (id_a, id_b), windows in pair_coherences.items():
            if not windows:
                continue
            mean_coh = sum(c for _, c in windows) / len(windows)
            i = receiver_ids.index(id_a)
            j = receiver_ids.index(id_b)
            if i < j:
                grid[i][j] = round(mean_coh, 6)
                grid[j][i] = round(mean_coh, 6)
            else:
                grid[j][i] = round(mean_coh, 6)
                grid[i][j] = round(mean_coh, 6)

        return {
            "receiver_order": receiver_ids,
            "grid": [[round(v, 6) for v in row] for row in grid],
            "dimensions": n,
        }
