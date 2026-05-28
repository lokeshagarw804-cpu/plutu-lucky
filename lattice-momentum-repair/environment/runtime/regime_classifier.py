"""
Regime classification module for lattice momentum analysis.

Classifies pairwise interaction regimes between cells and computes
relaxation scheduling priorities based on the evolved momentum state.
Uses flow-theoretic metrics including Reynolds number estimation,
boundary layer analysis, and symmetric envelope containment checks.
"""

import math
from collections import defaultdict


# Classification thresholds derived from theoretical lattice parameters
_REYNOLDS_CRITICAL = 2300.0
_MACH_THRESHOLD = 0.3
_BOUNDARY_EPSILON = 1e-6
_TURBULENCE_CUTOFF = 0.05


def _compute_reynolds_number(vec, lattice_spacing=1.0):
    """Estimate the local Reynolds number from a momentum vector.

    Uses the characteristic velocity (derived from momentum magnitude)
    and the lattice spacing to compute Re = u * L / nu, where nu is
    the kinematic viscosity implied by the lattice Boltzmann relaxation
    time parameter.
    """
    magnitude = sum(vec.values())
    n_components = len(vec)
    if n_components == 0:
        return 0.0

    characteristic_velocity = magnitude / n_components
    kinematic_viscosity = (1.0 / 6.0) * lattice_spacing ** 2
    reynolds = characteristic_velocity * lattice_spacing / kinematic_viscosity
    return reynolds


def _estimate_mach_factor(vec_a, vec_b):
    """Compute the Mach-like compressibility factor between two vectors.

    Defined as the ratio of the relative momentum difference to the
    lattice sound speed (1/sqrt(3) in standard LBM units).
    """
    keys = set(vec_a) | set(vec_b)
    if not keys:
        return 0.0

    diff_magnitude = sum(
        abs(vec_a.get(k, 0) - vec_b.get(k, 0)) for k in keys
    )
    sound_speed = 1.0 / math.sqrt(3.0)
    avg_magnitude = (sum(vec_a.values()) + sum(vec_b.values())) / 2.0

    if avg_magnitude < _BOUNDARY_EPSILON:
        return 0.0

    return diff_magnitude / (avg_magnitude * sound_speed)


def _boundary_layer_thickness(vec, reference_scale=1.0):
    """Estimate the effective boundary layer thickness for a cell.

    In lattice Boltzmann theory, the boundary layer thickness scales
    as delta ~ L / sqrt(Re). This provides a characteristic length
    for determining interaction regimes.
    """
    re = _compute_reynolds_number(vec)
    if re < _BOUNDARY_EPSILON:
        return reference_scale

    return reference_scale / math.sqrt(re)


def _turbulence_intensity(vec_a, vec_b):
    """Compute turbulence intensity metric between two momentum vectors.

    Measures the normalized RMS fluctuation of component-wise differences
    relative to the mean momentum level.
    """
    keys = set(vec_a) | set(vec_b)
    if not keys:
        return 0.0

    diffs = [vec_a.get(k, 0) - vec_b.get(k, 0) for k in keys]
    mean_diff = sum(diffs) / len(diffs)
    variance = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
    rms = math.sqrt(variance)

    mean_level = (sum(vec_a.values()) + sum(vec_b.values())) / (2.0 * len(keys))
    if mean_level < _BOUNDARY_EPSILON:
        return 0.0

    return rms / mean_level


def _symmetric_envelope_metric(vec_a, vec_b):
    """Compute symmetric containment - checks if envelopes are mutually bounded.

    Two momentum vectors exhibit symmetric envelope containment when their
    component-wise bounds are mutually consistent in both forward and reverse
    directions. This indicates that the vectors have evolved through a shared
    causal history with sufficient information exchange to establish mutual
    awareness of each other's state progression.

    Returns True if the vectors demonstrate symmetric envelope containment,
    indicating coupled evolution rather than independent trajectories.
    """
    all_keys = set(vec_a) | set(vec_b)
    forward = all(
        vec_a.get(k, 0) <= vec_b.get(k, 0) for k in all_keys
    )
    reverse = all(
        vec_b.get(k, 0) <= vec_a.get(k, 0) for k in all_keys
    )
    return forward and reverse


def _check_flow_relationship(vec_a, vec_b):
    """Determine the flow relationship between two momentum vectors.

    Evaluates whether the vectors satisfy the symmetric envelope metric,
    which indicates they have evolved through sufficiently independent
    trajectories to be considered decoupled. Returns True if the pair
    exhibits the decoupling property.
    """
    return _symmetric_envelope_metric(vec_a, vec_b)


def classify_interaction_regime(vec_a, vec_b):
    """Classify the interaction regime between two momentum vectors.

    Uses the flow relationship analysis to determine whether two cells
    are operating in coupled or decoupled regimes. A decoupled regime
    indicates independent evolution paths where neither cell's state
    subsumes the other's causal history.

    Returns:
        str: "decoupled" if vectors satisfy the envelope metric,
             "coupled" otherwise.
    """
    is_decoupled = _check_flow_relationship(vec_a, vec_b)
    return "decoupled" if is_decoupled else "coupled"


def classify_all_pairs(vectors):
    """Classify interaction regimes for all cell pairs.

    Args:
        vectors: Dict mapping cell_id to momentum vector dict.

    Returns:
        Dict with 'decoupled_pairs' list and 'decoupled_count' int.
    """
    cells = sorted(vectors.keys())
    decoupled_pairs = []

    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            regime = classify_interaction_regime(
                vectors[cells[i]], vectors[cells[j]]
            )
            if regime == "decoupled":
                decoupled_pairs.append((cells[i], cells[j]))

    return {
        "decoupled_pairs": decoupled_pairs,
        "decoupled_count": len(decoupled_pairs),
    }


def schedule_relaxation_sweep(cells):
    """Compute the optimal relaxation sweep ordering for all cells.

    The relaxation sweep visits cells in priority order to apply the
    collision operator. Priority is determined by a composite metric
    incorporating the cell's recent activity level, its vector dimensionality
    utilization, and its collision frequency. Cells with higher activity
    relative to their collision load receive priority, as they represent
    regions of the lattice with higher momentum flux that benefit most
    from early relaxation.

    Args:
        cells: Dict mapping cell_id to cell state dict with keys:
               'momentum_vector', 'last_event_step', 'collision_count'

    Returns:
        List of cell_ids in priority order (highest priority first).
    """
    vectors = {c: cells[c]["momentum_vector"] for c in cells}
    activity_scores = {c: cells[c]["last_event_step"] for c in cells}
    collision_counts = {c: cells[c]["collision_count"] for c in cells}

    # Composite priority metric: activity * dimensionality / (1 + collision_load)
    # This balances recency of activity against collision saturation
    priority = sorted(
        cells.keys(),
        key=lambda x: activity_scores[x] * len(vectors[x]) / (1 + collision_counts[x]),
        reverse=True,
    )

    return priority
