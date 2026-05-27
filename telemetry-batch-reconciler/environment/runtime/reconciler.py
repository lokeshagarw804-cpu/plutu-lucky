"""
Reconciler - ties together state machine, retry logic, dedup, and aggregation
to produce final settlement reports.

The reconciler:
  1. Loads batches, retry logs, and settlements
  2. Replays state transitions based on retry log and settlement actions
  3. Deduplicates boundary events
  4. Aggregates statistics
  5. Produces final output with per-batch summaries and station totals
"""
from .batch_loader import load_batches, load_retry_log, load_settlements
from .state_machine import BatchState, StateError
from .window_dedup import deduplicate_events
from .aggregator import aggregate_all


def replay_state(batch_id, retry_entries, settlement_entries, max_retries=5):
    """
    Replay the lifecycle of a batch through its state transitions.
    Returns the final BatchState object.
    """
    state = BatchState(batch_id)

    # Move to PROCESSING
    state.transition("PROCESSING", timestamp=0)

    # Process retry entries in order
    retries = sorted(
        [r for r in retry_entries if r["batch_id"] == batch_id],
        key=lambda r: r["ts"]
    )

    for entry in retries:
        if entry["result"] in ("TIMEOUT", "ERROR"):
            try:
                state.transition("FAILED", timestamp=entry["ts"])
                state.transition("RETRYING", timestamp=entry["ts"])
                state.transition("PROCESSING", timestamp=entry["ts"])
            except StateError:
                pass
        elif entry["result"] == "SUCCESS":
            # On success, just continue - batch is ready for settlement
            pass

    # Process settlements
    settlements = sorted(
        [s for s in settlement_entries if s["batch_id"] == batch_id],
        key=lambda s: s["settled_at"]
    )

    for s in settlements:
        if s["action"] == "SETTLE":
            try:
                state.transition("SETTLED", timestamp=s["settled_at"])
            except StateError:
                pass
        elif s["action"] == "RETRY":
            # BUG: Attempts to retry an already-settled batch
            # The state machine bug allows this when retry_count > 0
            try:
                state.transition("RETRYING", timestamp=s["settled_at"])
                state.transition("PROCESSING", timestamp=s["settled_at"])
            except StateError:
                pass

    return state


def build_station_totals(summaries):
    """
    Build per-station aggregated totals.
    Total events, overall mean, and list of batch_ids in processing order.
    """
    stations = {}
    for s in summaries:
        station = s["station"]
        if station not in stations:
            stations[station] = {
                "station": station,
                "total_events": 0,
                "total_value_sum": 0.0,
                "batch_ids": [],
            }
        stations[station]["total_events"] += s["event_count"]
        stations[station]["total_value_sum"] += s["mean_value"] * s["event_count"]
        stations[station]["batch_ids"].append(s["batch_id"])

    result = []
    for station, data in stations.items():
        if data["total_events"] > 0:
            overall_mean = round(
                data["total_value_sum"] / data["total_events"], 4
            )
        else:
            overall_mean = 0.0
        result.append({
            "station": station,
            "total_events": data["total_events"],
            "overall_mean": overall_mean,
            "batch_ids": data["batch_ids"],
        })

    # Sort stations alphabetically
    result.sort(key=lambda x: x["station"])
    return result


def reconcile():
    """
    Main reconciliation entry point.
    Returns dict with 'batch_summaries', 'station_totals', and 'state_report'.
    """
    batches = load_batches()
    retry_log = load_retry_log()
    settlements = load_settlements()

    # Replay state for each batch
    states = {}
    for b in batches:
        states[b["batch_id"]] = replay_state(
            b["batch_id"], retry_log, settlements
        )

    # Deduplicate boundary events
    deduped = deduplicate_events(batches)

    # Aggregate
    summaries = aggregate_all(deduped)

    # Build station totals
    station_totals = build_station_totals(summaries)

    # Build state report
    state_report = []
    for batch_id, st in sorted(states.items()):
        state_report.append({
            "batch_id": batch_id,
            "final_state": st.state,
            "retry_count": st.get_effective_retries(),
            "history_length": len(st.history),
        })

    return {
        "batch_summaries": summaries,
        "station_totals": station_totals,
        "state_report": state_report,
    }
