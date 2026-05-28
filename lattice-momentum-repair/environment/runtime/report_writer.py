"""
Report generation module for lattice momentum simulation output.

Produces structured output files containing per-cell state dumps and
flow analysis reports with cryptographic digests for validation.
"""

import json
import hashlib
import os


def _format_momentum_vector(vector):
    """Format a momentum vector for canonical serialization.

    Ensures deterministic key ordering for digest computation.
    """
    return {k: vector[k] for k in sorted(vector.keys())}


def _compute_magnitude(vector):
    """Compute the total momentum magnitude (L1 norm)."""
    return sum(vector.values())


def _compute_component_variance(vector):
    """Compute the variance of momentum components.

    Used for diagnostic annotations in the flow report.
    """
    values = list(vector.values())
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def _format_pair_label(cell_a, cell_b):
    """Generate canonical pair label for report entries."""
    return f"{cell_a}<->{cell_b}"


def _build_canonical_state(states):
    """Build the canonical state representation for digest computation.

    The canonical form sorts cells alphabetically and formats vectors
    with sorted keys, ensuring deterministic digest generation.
    """
    canonical = {}
    for cell_id in sorted(states.keys()):
        state = states[cell_id]
        canonical[cell_id] = _format_momentum_vector(state["momentum_vector"])
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def _compute_digest(canonical_state):
    """Compute SHA-256 digest of the canonical simulation state."""
    return hashlib.sha256(canonical_state.encode("utf-8")).hexdigest()


def _generate_statistics_block(states):
    """Generate aggregate statistics for the report metadata section."""
    magnitudes = {}
    variances = {}
    for cell_id, state in states.items():
        vec = state["momentum_vector"]
        magnitudes[cell_id] = _compute_magnitude(vec)
        variances[cell_id] = round(_compute_component_variance(vec), 4)

    total_magnitude = sum(magnitudes.values())
    avg_magnitude = total_magnitude / len(magnitudes) if magnitudes else 0

    return {
        "total_system_momentum": total_magnitude,
        "average_cell_magnitude": round(avg_magnitude, 4),
        "component_variances": variances,
    }


def write_lattice_state(states, output_dir):
    """Write per-cell state snapshots to lattice_state.jsonl.

    Each line contains one JSON object with cell state information
    including momentum vector, event counts, and metadata.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "lattice_state.jsonl")

    with open(filepath, "w") as fh:
        for cell_id in sorted(states.keys()):
            state = states[cell_id]
            record = {
                "cell_id": state["cell_id"],
                "momentum_vector": _format_momentum_vector(
                    state["momentum_vector"]
                ),
                "total_events": state["total_events"],
                "last_event_step": state["last_event_step"],
            }
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    return filepath


def write_flow_report(states, classification_result, priority_order, output_dir):
    """Write the flow analysis report with regime classification results.

    Includes decoupled pair analysis, relaxation priority ordering,
    magnitude map, and the simulation state digest.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "flow_report.json")

    # Compute magnitudes
    magnitude_map = {}
    for cell_id in sorted(states.keys()):
        vec = states[cell_id]["momentum_vector"]
        magnitude_map[cell_id] = _compute_magnitude(vec)

    # Build canonical state and compute digest
    canonical = _build_canonical_state(states)
    digest = _compute_digest(canonical)

    # Format decoupled pairs
    formatted_pairs = [
        _format_pair_label(a, b)
        for a, b in classification_result["decoupled_pairs"]
    ]

    report = {
        "decoupled_pairs": formatted_pairs,
        "decoupled_count": classification_result["decoupled_count"],
        "relaxation_priority": priority_order,
        "magnitude_map": magnitude_map,
        "digest": digest,
        "statistics": _generate_statistics_block(states),
    }

    with open(filepath, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)

    return filepath
