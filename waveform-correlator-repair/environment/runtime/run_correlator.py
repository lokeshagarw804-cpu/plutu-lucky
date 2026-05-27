"""Seismic waveform coherence pipeline — main entry point.

Orchestrates the full waveform analysis: load and prepare receiver traces,
compute pairwise windowed coherence, assemble the coherence grid, and
detect sustained coherence phases.
"""
import json
import os
from itertools import combinations

from runtime.trace_loader import TraceLoader
from runtime.coherence_engine import CoherenceEngine
from runtime.grid_builder import GridBuilder
from runtime.phase_detector import PhaseDetector


def main():
    config_path = "/app/runtime/config.ini"

    # Stage 1: Load, filter, and whiten all receiver traces
    loader = TraceLoader(config_path)
    traces = loader.load_traces()

    # Stage 2: Compute pairwise windowed coherence
    engine = CoherenceEngine(config_path)
    receiver_ids = sorted(traces.keys())
    pair_coherences = {}

    for id_a, id_b in combinations(receiver_ids, 2):
        windows = engine.compute_coherence(traces[id_a], traces[id_b])
        pair_coherences[(id_a, id_b)] = windows

    # Stage 3: Build coherence grid
    builder = GridBuilder()
    grid_result = builder.build_grid(traces, pair_coherences)

    # Stage 4: Detect sustained coherence phases
    detector = PhaseDetector(config_path)
    phases = detector.detect_phases(pair_coherences)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "coherence_grid.json"), "w") as f:
        json.dump(grid_result, f, indent=2)

    phase_output = {
        "threshold": detector._threshold,
        "min_duration_windows": detector._min_duration,
        "total_phases": len(phases),
        "phases": phases,
    }
    with open(os.path.join(output_dir, "detected_phases.json"), "w") as f:
        json.dump(phase_output, f, indent=2)


if __name__ == "__main__":
    main()
