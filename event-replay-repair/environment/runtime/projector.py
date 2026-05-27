"""Event projector — extracts relevant fields from event payloads.

Applies projection rules to filter event payloads down to the configured
target fields. Only payload keys matching the projection target_fields
configuration are retained for downstream aggregation.
"""
import configparser


class EventProjector:
    """Projects event payloads to configured target fields."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_fields = self._config.get("projection", "target_fields")
        self._target_fields = set(raw_fields.split(","))

    def project_event(self, event):
        """Extract target fields from event payload.

        Returns a projected record containing only the fields listed
        in the projection configuration, plus event metadata.
        """
        payload = event["payload"]
        projected = {}

        for key, value in payload.items():
            if key in self._target_fields:
                projected[key] = value

        return {
            "event_id": event["event_id"],
            "timestamp": event["timestamp"],
            "stream_id": event["stream_id"],
            "entity_id": event["entity_id"],
            "type": event["type"],
            "projected_fields": projected,
        }

    def project_batch(self, events):
        """Project all events in a batch."""
        return [self.project_event(e) for e in events]
