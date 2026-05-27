"""Trip segmenter — splits telemetry pings into discrete trips.

A trip boundary occurs when the time gap between consecutive pings
exceeds the configured idle threshold. Pings at exactly the threshold
gap belong to the current trip.
"""
import configparser


class TripSegmenter:
    """Segments vehicle pings into trips based on idle gaps."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._idle_threshold = self._config.getint(
            "segmentation", "idle_threshold_seconds"
        )
        self._min_pings = self._config.getint(
            "segmentation", "min_pings_per_trip"
        )

    def segment(self, pings):
        """Split pings into trip segments.

        Returns list of trips, each trip is a list of pings.
        A new trip starts when gap between consecutive pings
        exceeds the idle threshold.
        """
        if not pings:
            return []

        trips = []
        current_trip = [pings[0]]

        for i in range(1, len(pings)):
            gap = pings[i]["timestamp"] - pings[i - 1]["timestamp"]
            if gap >= self._idle_threshold:
                if len(current_trip) >= self._min_pings:
                    trips.append(current_trip)
                current_trip = [pings[i]]
            else:
                current_trip.append(pings[i])

        if len(current_trip) >= self._min_pings:
            trips.append(current_trip)

        return trips
