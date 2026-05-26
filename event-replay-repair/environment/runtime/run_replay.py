"""Main entry point for the event replay materialization system."""
from runtime.loader import EventLoader
from runtime.correlator import EventCorrelator
from runtime.projector import EventProjector
from runtime.materializer import Materializer


def main():
    """Run the full event replay and materialization process."""
    config_path = "/app/runtime/config.ini"

    loader = EventLoader(config_path)
    events = loader.load_all()

    correlator = EventCorrelator(config_path)
    timeline = correlator.correlate(events)

    projector = EventProjector(config_path)
    aggregates = projector.project(timeline)

    materializer = Materializer(config_path)
    materializer.materialize(aggregates, timeline)


if __name__ == "__main__":
    main()
