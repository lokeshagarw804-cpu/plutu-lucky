"""Event ledger replay engine — main entry point.

Orchestrates the full ledger reconciliation process: load event streams,
merge and sort events, validate and deduplicate, aggregate into time
windows, run reconciliation checks, and generate output reports.
"""
from runtime.loader import EventStreamLoader
from runtime.sorter import EventSorter
from runtime.validator import EventValidator
from runtime.aggregator import WindowAggregator
from runtime.reconciler import Reconciler
from runtime.reporter import ReportGenerator


def main():
    config_path = "/app/runtime/config.ini"

    # Load event streams
    loader = EventStreamLoader(config_path)
    streams = loader.load_streams()

    # Merge and sort all events
    sorter = EventSorter()
    sorted_events = sorter.merge_events(streams)

    # Validate and deduplicate
    validator = EventValidator(config_path)
    clean_events = validator.validate_and_dedupe(sorted_events)

    # Aggregate into time windows
    aggregator = WindowAggregator(config_path)
    windows = aggregator.aggregate(clean_events)

    # Run reconciliation
    reconciler = Reconciler(config_path)
    anomalies = reconciler.reconcile(windows)

    # Generate reports
    output_dir = "/app/runtime/output"
    reporter = ReportGenerator(output_dir)
    reporter.generate(windows, anomalies, len(streams), len(clean_events))

    print(f"Processed {len(streams)} streams, {len(clean_events)} events")
    print(f"Windows: {len(windows)}, Anomalies: {len(anomalies)}")


if __name__ == "__main__":
    main()
