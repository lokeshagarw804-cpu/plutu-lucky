"""View materializer — builds final materialized view from snapshots.

Assembles the final projected state from batch snapshots. The snapshot
mode determines how batch results combine into the final view.
"""
import configparser


class ViewMaterializer:
    """Builds materialized view from projection snapshots."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._snapshot_mode = self._config.get("replay", "snapshot_mode")

    def materialize(self, snapshots):
        """Build final materialized view from batch snapshots.

        Combines snapshot state according to configured snapshot_mode.
        Returns the materialized view dictionary.
        """
        if not snapshots:
            return {}

        if self._snapshot_mode == "final":
            return snapshots[-1]

        # Cumulative: sum totals across all snapshots
        result = {}
        for snapshot in snapshots:
            for stream_id, stream_state in snapshot.items():
                if stream_id not in result:
                    result[stream_id] = {
                        "event_count": 0,
                        "entities": {},
                        "totals": {},
                    }
                result[stream_id]["event_count"] += stream_state["event_count"]
                result[stream_id]["entities"].update(stream_state["entities"])
                for key, value in stream_state["totals"].items():
                    result[stream_id]["totals"][key] = (
                        result[stream_id]["totals"].get(key, 0) + value
                    )
        return result
