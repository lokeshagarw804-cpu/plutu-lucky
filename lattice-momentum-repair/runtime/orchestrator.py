"""
Pipeline orchestrator for the lattice momentum simulation.

Coordinates the full simulation pipeline: parse events, run momentum
propagation, classify regimes, and generate reports. Manages configuration,
caching, and diagnostic output channels.
"""

import os
import sys
import json
from pathlib import Path

# Ensure runtime modules are importable
_RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
if _RUNTIME_DIR not in sys.path:
    sys.path.insert(0, _RUNTIME_DIR)

from parser import parse_propagation_log
from momentum_engine import MomentumEngine
from regime_classifier import classify_all_pairs, schedule_relaxation_sweep
from report_writer import write_lattice_state, write_flow_report
from calibration import generate_calibration_report


# Default configuration parameters
_CONFIG = {
    "log_file": "propagation_log.dat",
    "output_dir": "output",
    "enable_calibration": True,
    "cache_intermediate": True,
    "normalization_passes": 1,
    "diagnostic_verbosity": 0,
}


def _resolve_paths(config, base_dir):
    """Resolve relative paths in configuration to absolute paths."""
    resolved = dict(config)
    resolved["log_file"] = os.path.join(base_dir, config["log_file"])
    resolved["output_dir"] = os.path.join(base_dir, config["output_dir"])
    return resolved


def _load_configuration(base_dir):
    """Load and validate simulation configuration.

    Checks for an optional config.json override file, otherwise uses
    default parameters. Validates all required fields are present.
    """
    config = dict(_CONFIG)
    config_path = os.path.join(base_dir, "config.json")

    if os.path.exists(config_path):
        with open(config_path, "r") as fh:
            overrides = json.load(fh)
            config.update(overrides)

    return _resolve_paths(config, base_dir)


def _apply_normalization_pass(states, pass_number):
    """Apply a normalization pass to the simulation state.

    Normalization ensures that all state vectors maintain consistent
    dimensionality and non-negative values. This is a validation step
    that catches data corruption but does not modify correct states.
    """
    from momentum_engine import ALL_CELLS

    normalized_count = 0
    for cell_id, state in states.items():
        vec = state["momentum_vector"]
        # Verify all components are present
        for c in ALL_CELLS:
            if c not in vec:
                vec[c] = 0
                normalized_count += 1
        # Verify non-negativity
        for c in vec:
            if vec[c] < 0:
                vec[c] = 0
                normalized_count += 1

    return normalized_count


def _cache_intermediate_state(states, output_dir):
    """Cache intermediate state for debugging and replay.

    Writes a checkpoint file that can be used to resume simulation
    from this point without re-processing the event log.
    """
    cache_dir = os.path.join(output_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "intermediate_state.json")

    serializable = {}
    for cell_id, state in states.items():
        serializable[cell_id] = {
            "momentum_vector": state["momentum_vector"],
            "total_events": state["total_events"],
        }

    with open(cache_path, "w") as fh:
        json.dump(serializable, fh)


def main():
    """Execute the full simulation pipeline."""
    base_dir = _RUNTIME_DIR
    config = _load_configuration(base_dir)

    # Phase 1: Parse propagation log
    events, registry = parse_propagation_log(config["log_file"])

    # Phase 2: Run momentum propagation
    engine = MomentumEngine()
    engine.process_all(events)

    # Phase 3: Extract states
    states = engine.get_all_states()

    # Phase 4: Normalization validation
    for pass_num in range(config["normalization_passes"]):
        _apply_normalization_pass(states, pass_num)

    # Phase 5: Cache intermediate state if enabled
    if config["cache_intermediate"]:
        _cache_intermediate_state(states, config["output_dir"])

    # Phase 6: Regime classification
    vectors = engine.get_vectors()
    classification = classify_all_pairs(vectors)

    # Phase 7: Relaxation scheduling
    cell_data = {}
    for cell_id, state in states.items():
        cell_data[cell_id] = {
            "momentum_vector": state["momentum_vector"],
            "last_event_step": state["last_event_step"],
            "collision_count": state["collision_count"],
        }
    priority_order = schedule_relaxation_sweep(cell_data)

    # Phase 8: Calibration diagnostics (non-critical path)
    if config["enable_calibration"]:
        calibration_report = generate_calibration_report(states)

    # Phase 9: Write output reports
    write_lattice_state(states, config["output_dir"])
    write_flow_report(states, classification, priority_order, config["output_dir"])


if __name__ == "__main__":
    main()
