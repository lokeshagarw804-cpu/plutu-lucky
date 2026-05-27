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
                # First batch keeps all events in its window
                # BUG: uses < instead of <= for window_end check
                # This DROPS the boundary event from the first batch
                filtered = [
                    e for e in batch["events"]
                    if e["ts"] >= batch["window_start"] and e["ts"] < batch["window_end"]
                ]
            else:
                prev_batch = sorted_batches[i - 1]
                # Later batches exclude events at the shared boundary
                # BUG: uses >= instead of > for window_start boundary
                # Combined with the bug above, boundary events get LOST entirely
                filtered = [
                    e for e in batch["events"]
                    if e["ts"] >= batch["window_start"] and e["ts"] <= batch["window_end"]
                ]

            result.append({**batch, "events": filtered})

    return result
