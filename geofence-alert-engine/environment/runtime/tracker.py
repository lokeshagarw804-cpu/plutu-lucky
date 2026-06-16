"""Dwell time tracker — monitors vehicle presence within geofence zones.

Implements a state machine for each vehicle-zone pair to track entry,
confirmed presence (dwell), and exit events. Computes total dwell
duration and number of confirmed interior readings.
"""
import configparser


class DwellTracker:
    """Tracks vehicle dwell time within geofence zones using state machine."""

    OUTSIDE = 0
    ENTERING = 1
    INSIDE = 2
    EXITING = 3

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._confirm_count = self._config.getint("alerts", "confirmation_readings")

    def compute_dwells(self, annotated_readings):
        """Compute dwell metrics for each vehicle-zone pair.

        Tracks state transitions and accumulates dwell time for vehicles
        that achieve confirmed INSIDE state.
        """
        # State per (vehicle_id, zone_id)
        states = {}
        metrics = {}

        # Process readings in temporal order
        for reading in annotated_readings:
            vid = reading["vehicle_id"]
            epoch = reading["epoch"]
            zones_now = set(reading.get("zones", []))

            # Get all zones this vehicle has been tracked in
            known_zones = set()
            for key in states:
                if key[0] == vid:
                    known_zones.add(key[1])
            all_zones = known_zones | zones_now

            for zone_id in all_zones:
                key = (vid, zone_id)
                if key not in states:
                    states[key] = {
                        "state": self.OUTSIDE,
                        "confirm_counter": 0,
                        "entry_epoch": None,
                    }
                if key not in metrics:
                    metrics[key] = {
                        "vehicle_id": vid,
                        "zone_id": zone_id,
                        "dwell_seconds": 0,
                        "readings_inside": 0,
                    }

                state_info = states[key]
                is_inside = zone_id in zones_now

                self._transition(state_info, metrics[key], is_inside, epoch)

        return list(metrics.values())

    def _transition(self, state_info, metric, is_inside, epoch):
        """Apply state machine transition for a single reading.

        State transitions:
            OUTSIDE + inside reading -> ENTERING (start confirmation)
            ENTERING + inside reading -> INSIDE (if confirmed) or stay ENTERING
            INSIDE + inside reading -> stay INSIDE (accumulate dwell)
            INSIDE + outside reading -> EXITING
            EXITING + outside reading -> OUTSIDE
            EXITING + inside reading -> INSIDE (re-entry)
        """
        current_state = state_info["state"]

        # Reset confirmation counter on each evaluation pass
        if current_state == self.OUTSIDE:
            state_info["confirm_counter"] = 0
            if is_inside:
                state_info["state"] = self.ENTERING
                state_info["confirm_counter"] = 1
                state_info["entry_epoch"] = epoch

        elif current_state == self.ENTERING:
            state_info["confirm_counter"] = 0
            if is_inside:
                state_info["confirm_counter"] += 1
                if state_info["confirm_counter"] >= self._confirm_count:
                    state_info["state"] = self.INSIDE
                    metric["readings_inside"] += 1
            else:
                state_info["state"] = self.OUTSIDE
                state_info["entry_epoch"] = None

        elif current_state == self.INSIDE:
            if is_inside:
                metric["readings_inside"] += 1
                metric["dwell_seconds"] = epoch - state_info["entry_epoch"]
            else:
                state_info["state"] = self.EXITING
                metric["dwell_seconds"] = epoch - state_info["entry_epoch"]

        elif current_state == self.EXITING:
            if is_inside:
                state_info["state"] = self.INSIDE
                metric["readings_inside"] += 1
            else:
                state_info["state"] = self.OUTSIDE
                state_info["confirm_counter"] = 0
                state_info["entry_epoch"] = None
