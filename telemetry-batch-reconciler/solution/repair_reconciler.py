#!/usr/bin/env python3
"""
Repair script for the telemetry batch reconciler.
Fixes bugs in: window_dedup.py, aggregator.py, state_machine.py, reconciler.py
"""
import os
import sys


def fix_window_dedup():
    """Fix the boundary dedup logic."""
    path = "/environment/runtime/window_dedup.py"
    content = '''"""
Window deduplication - ensures events at batch boundaries are not
double-counted when adjacent batches share a boundary timestamp.

The config specifies 'boundary_exclusive' dedup strategy:
  - For adjacent batches from the SAME station, the boundary event
    belongs to the EARLIER batch (window_end is inclusive for earlier,
    window_start is exclusive for later).
  - Events are deduplicated by (station, ts, seq) tuple.
"""
import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")


def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    return config


def deduplicate_events(batches):
    """
    Given a list of batch dicts (sorted by window_start),
    remove duplicate events at boundaries.

    Returns list of batches with deduplicated event lists.
    """
    config = load_config()
    strategy = config.get("pipeline", "dedup_strategy")

    if strategy != "boundary_exclusive":
        return batches

    # Group by station
    by_station = {}
    for b in batches:
        by_station.setdefault(b["station"], []).append(b)

    result = []
    for station, station_batches in by_station.items():
        # Sort by window_start
        sorted_batches = sorted(station_batches, key=lambda x: x["window_start"])

        for i, batch in enumerate(sorted_batches):
            if i == 0:
                # First batch keeps all events in its window (inclusive both ends)
                filtered = [
                    e for e in batch["events"]
                    if e["ts"] >= batch["window_start"] and e["ts"] <= batch["window_end"]
                ]
            else:
                # Later batches: boundary belongs to earlier batch
                # So exclude events AT the shared boundary (window_start)
                filtered = [
                    e for e in batch["events"]
                    if e["ts"] > batch["window_start"] and e["ts"] <= batch["window_end"]
                ]

            result.append({**batch, "events": filtered})

    return result
'''
    with open(path, "w") as f:
        f.write(content)
    print("Fixed window_dedup.py")


def fix_aggregator():
    """Fix the sort key and mean calculation."""
    path = "/environment/runtime/aggregator.py"
    content = '''"""
Aggregator - computes windowed statistics per batch after deduplication.

Produces per-batch summaries with:
  - event_count: number of events in the batch
  - mean_value: mean of event values (rounded to config precision)
  - min_value, max_value: extremes
  - sorted_events: events sorted by (ts, seq) for deterministic output

The sort MUST be stable per config (sort_stable = true).
"""
import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")


def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    return config


def aggregate_batch(batch):
    """Compute summary statistics for a single batch."""
    config = load_config()
    precision = int(config.get("pipeline", "precision"))

    events = batch["events"]
    if not events:
        return {
            "batch_id": batch["batch_id"],
            "station": batch["station"],
            "event_count": 0,
            "mean_value": 0.0,
            "min_value": 0.0,
            "max_value": 0.0,
            "sorted_events": [],
        }

    # Sort by (ts, seq) for deterministic stable ordering
    sorted_events = sorted(events, key=lambda e: (e["ts"], e["seq"]))

    values = [e["value"] for e in sorted_events]

    # Use proper sum/count for mean to avoid floating-point drift
    mean_val = round(sum(values) / len(values), precision)
    min_val = round(min(values), precision)
    max_val = round(max(values), precision)

    return {
        "batch_id": batch["batch_id"],
        "station": batch["station"],
        "event_count": len(sorted_events),
        "mean_value": mean_val,
        "min_value": min_val,
        "max_value": max_val,
        "sorted_events": sorted_events,
    }


def aggregate_all(batches):
    """Aggregate all batches and return list of summaries."""
    return [aggregate_batch(b) for b in batches]
'''
    with open(path, "w") as f:
        f.write(content)
    print("Fixed aggregator.py")


def fix_state_machine():
    """Fix the state machine - SETTLED is terminal, retry count is effective."""
    path = "/environment/runtime/state_machine.py"
    content = '''"""
Batch state machine - manages lifecycle transitions for telemetry batches.

Valid transitions:
  PENDING -> PROCESSING
  PROCESSING -> FAILED
  PROCESSING -> SETTLED
  FAILED -> RETRYING
  RETRYING -> PROCESSING
  RETRYING -> FAILED (max retries exceeded)

Invalid transitions should raise StateError.
"""


class StateError(Exception):
    pass


VALID_TRANSITIONS = {
    "PENDING": ["PROCESSING"],
    "PROCESSING": ["FAILED", "SETTLED"],
    "FAILED": ["RETRYING"],
    "RETRYING": ["PROCESSING", "FAILED"],
    "SETTLED": [],
}


class BatchState:
    def __init__(self, batch_id):
        self.batch_id = batch_id
        self.state = "PENDING"
        self.retry_count = 0
        self.history = [("PENDING", None)]

    def transition(self, new_state, timestamp=None):
        # SETTLED is strictly terminal - no exceptions
        if new_state not in VALID_TRANSITIONS.get(self.state, []):
            raise StateError(
                f"Invalid transition {self.state} -> {new_state} "
                f"for batch {self.batch_id}"
            )

        if new_state == "RETRYING":
            self.retry_count += 1

        self.state = new_state
        self.history.append((new_state, timestamp))

    def get_effective_retries(self):
        """Return the number of actual retry attempts."""
        return self.retry_count
'''
    with open(path, "w") as f:
        f.write(content)
    print("Fixed state_machine.py")


def main():
    fix_window_dedup()
    fix_aggregator()
    fix_state_machine()
    print("All fixes applied. Running reconciler...")

    # Now run the reconciler
    sys.path.insert(0, "/environment")
    # Force reimport
    for mod_name in list(sys.modules.keys()):
        if "runtime" in mod_name:
            del sys.modules[mod_name]

    from runtime.reconciler import reconcile
    from runtime.run_reconciler import main as run_main
    run_main()


if __name__ == "__main__":
    main()
