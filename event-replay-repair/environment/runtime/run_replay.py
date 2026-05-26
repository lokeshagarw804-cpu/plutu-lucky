"""
Main entry point for the event replay projection system.

Orchestrates the full event sourcing replay process:
1. Load events from all stream source files
2. Filter events by configured allowed types
3. Sort events into deterministic replay order
4. Build materialized projections via batch replay
5. Generate output reports
"""

from runtime.loader import load_events
from runtime.filter import EventFilter
from runtime.sorter import EventSorter
from runtime.projector import Projector
from runtime.reporter import ReplayReporter


def main():
    """Run the event replay projection process."""
    # Stage 1: Load all events from stream files
    events = load_events()

    # Stage 2: Filter by allowed event types
    event_filter = EventFilter()
    filtered = event_filter.filter_events(events)

    # Stage 3: Sort into replay order
    sorter = EventSorter()
    sorted_events = sorter.sort_events(filtered)

    # Stage 4: Build projections
    projector = Projector()
    projections = projector.build_projections(sorted_events)
    final_state = projector.get_final_state()
    batch_totals = projector.get_batch_totals()

    # Stage 5: Generate reports
    reporter = ReplayReporter()
    event_log, summary = reporter.generate_reports(
        sorted_events, projections, final_state, batch_totals
    )

    print(f"Processed {event_log['total_events']} events")
    print(f"Batches: {summary['total_batches']}")
    print(f"Entities tracked: {summary['total_entities']}")
    print(f"Streams: {list(summary['stream_counts'].keys())}")


if __name__ == "__main__":
    main()
