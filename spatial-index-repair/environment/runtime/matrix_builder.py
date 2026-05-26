"""Correlation matrix builder — assembles pairwise correlations.

Builds an upper-triangle correlation matrix from all station pairs,
computing the mean correlation across all windows for each pair.
"""
from itertools import combinations


class MatrixBuilder:
    """Builds the station-pair correlation matrix."""

    def build_matrix(self, stations, pair_correlations):
        """Construct correlation matrix from pairwise window correlations.

        Stations are sorted by identifier for consistent matrix layout.
        Returns dict with station_order and matrix values.
        """
        station_ids = sorted(stations.keys())
        n = len(station_ids)

        # Initialize matrix
        matrix = [[0.0] * n for _ in range(n)]

        # Fill diagonal with 1.0
        for i in range(n):
            matrix[i][i] = 1.0

        # Fill upper triangle from computed correlations
        for (id_a, id_b), windows in pair_correlations.items():
            if not windows:
                continue
            mean_corr = sum(c for _, c in windows) / len(windows)
            i = station_ids.index(id_a)
            j = station_ids.index(id_b)
            if i < j:
                matrix[i][j] = round(mean_corr, 6)
                matrix[j][i] = round(mean_corr, 6)
            else:
                matrix[j][i] = round(mean_corr, 6)
                matrix[i][j] = round(mean_corr, 6)

        return {
            "station_order": station_ids,
            "matrix": [[round(v, 6) for v in row] for row in matrix],
            "size": n,
        }
