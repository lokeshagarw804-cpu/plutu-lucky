"""Pipeline pressure monitor — main entry point.

Orchestrates the full pressure monitoring pipeline: load segment data,
map sensors to segments, interpolate readings, compute gradients,
aggregate in rolling windows, and detect anomalous events.
"""
import json
import os

from runtime.loader import PipelineLoader
from runtime.segment_mapper import SegmentMapper
from runtime.interpolator import CubicInterpolator
from runtime.gradient_calculator import GradientCalculator
from runtime.aggregator import RollingAggregator
from runtime.threshold_engine import ThresholdEngine


def main():
    config_path = "/app/runtime/config.ini"

    # Load raw segment data
    loader = PipelineLoader(config_path)
    raw_segments = loader.load_segments()

    # Map sensors to segments and compute averages
    mapper = SegmentMapper(config_path)
    mapped = mapper.map_segments(raw_segments)

    # Interpolate pressure readings for higher resolution
    interpolator = CubicInterpolator(config_path)
    interpolated = {}
    for seg_id, seg_data in mapped.items():
        upsampled = interpolator.interpolate_segment(
            seg_data["averaged_readings"],
            seg_data["sample_interval"],
        )
        interpolated[seg_id] = {
            **seg_data,
            "averaged_readings": upsampled,
        }

    # Compute pressure gradients
    calculator = GradientCalculator(config_path)
    gradients = calculator.compute_gradients(interpolated)

    # Aggregate in rolling windows
    aggregator = RollingAggregator(config_path)
    aggregated = aggregator.aggregate(gradients)

    # Detect anomalous events
    engine = ThresholdEngine(config_path)
    events = engine.detect_events(aggregated)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    # Segment ordering: numeric sort by suffix
    segment_order = sorted(
        mapped.keys(), key=lambda s: int(s.split("_")[1])
    )

    # Build summary report
    summary = {
        "segment_order": segment_order,
        "total_segments": len(segment_order),
        "total_events": len(events),
        "events_by_type": {
            "surge": len([e for e in events if e["type"] == "surge"]),
            "leak": len([e for e in events if e["type"] == "leak"]),
        },
        "per_segment_windows": {
            seg_id: aggregated[seg_id]["total_windows"]
            for seg_id in segment_order
        },
    }

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Write detailed events
    event_output = {
        "threshold": 2.5,
        "min_duration_samples": 3,
        "total_events": len(events),
        "events": sorted(events, key=lambda e: (e["segment_id"], e["start_window"])),
    }

    with open(os.path.join(output_dir, "events.json"), "w") as f:
        json.dump(event_output, f, indent=2)

    # Write per-segment gradient statistics
    gradient_stats = {}
    for seg_id in segment_order:
        if seg_id in gradients:
            grad_vals = gradients[seg_id]["gradient_values"]
            magnitudes = [abs(v) for v in grad_vals]
            gradient_stats[seg_id] = {
                "num_gradient_samples": len(grad_vals),
                "max_magnitude": round(max(magnitudes), 6) if magnitudes else 0.0,
                "mean_magnitude": round(
                    sum(magnitudes) / len(magnitudes), 6
                ) if magnitudes else 0.0,
                "total_windows": aggregated[seg_id]["total_windows"],
            }

    with open(os.path.join(output_dir, "gradient_stats.json"), "w") as f:
        json.dump(gradient_stats, f, indent=2)


if __name__ == "__main__":
    main()
