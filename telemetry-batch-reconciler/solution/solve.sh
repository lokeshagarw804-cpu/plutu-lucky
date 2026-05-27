#!/usr/bin/env bash

# Repair the telemetry batch reconciler pipeline
# Fixes window dedup, aggregator sort/mean, and state machine bugs

echo "=== Telemetry Batch Reconciler Repair ==="
echo "Diagnosing issues..."

# Check the current broken output first
echo "Running current (broken) reconciler..."
pushd /environment > /dev/null
python3 -c "
import sys
sys.path.insert(0, '.')
from runtime.reconciler import reconcile
import json
result = reconcile()
print('Current state report:')
for sr in result['state_report']:
    print(f\"  {sr['batch_id']}: state={sr['final_state']}, retries={sr['retry_count']}\")
print('Current station totals:')
for st in result['station_totals']:
    print(f\"  {st['station']}: {st['total_events']} events, mean={st['overall_mean']}\")
" 2>&1 || echo "Current run had errors"
popd > /dev/null

echo ""
echo "Applying fixes..."

# Fix 1: window_dedup.py - boundary logic
# The first batch uses < instead of <= for window_end (drops boundary event)
# Later batches use >= instead of > for window_start (includes boundary that belongs to earlier)
cat > /environment/runtime/window_dedup.py << 'PYEOF'
"""
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
                # First batch: inclusive both ends
                filtered = [
                    e for e in batch["events"]
                    if e["ts"] >= batch["window_start"] and e["ts"] <= batch["window_end"]
                ]
            else:
                # Later batches: boundary belongs to earlier batch
                # Exclude events at window_start (shared boundary)
                filtered = [
                    e for e in batch["events"]
                    if e["ts"] > batch["window_start"] and e["ts"] <= batch["window_end"]
                ]

            result.append({**batch, "events": filtered})

    return result
PYEOF
echo "  Fixed window_dedup.py (boundary inclusive/exclusive logic)"

# Fix 2: aggregator.py - sort key and mean calculation
# Sort was using only 'ts' without 'seq' tiebreaker
# Mean was using incremental calculation causing precision drift
cat > /environment/runtime/aggregator.py << 'PYEOF'
"""
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

    # Use proper sum/len for mean calculation
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
PYEOF
echo "  Fixed aggregator.py (sort key + mean calculation)"

# Fix 3: state_machine.py - terminal state enforcement and retry counting
# SETTLED was incorrectly allowing transitions when retry_count > 0
# retry_count was cumulative instead of per-cycle effective count
cat > /environment/runtime/state_machine.py << 'PYEOF'
"""
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
        # Strictly enforce valid transitions - SETTLED is terminal
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
PYEOF
echo "  Fixed state_machine.py (terminal state + retry count)"

echo ""
echo "Running repaired reconciler..."

# Run the fixed version
pushd /environment > /dev/null
python3 -c "
import sys
sys.path.insert(0, '.')

# Clear cached modules
for mod in list(sys.modules.keys()):
    if 'runtime' in mod:
        del sys.modules[mod]

from runtime.run_reconciler import main
main()
"
popd > /dev/null

echo ""
echo "=== Repair complete ==="
