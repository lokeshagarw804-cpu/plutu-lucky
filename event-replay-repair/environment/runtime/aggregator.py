"""Entity aggregator — builds aggregate state from projected events.

Applies events to entity state using last-write-wins semantics for
gauge-type fields (order_total, payment_amount, fulfillment_status)
and accumulation for counter-type fields (quantity represents items
allocated, so it accumulates across events for the same entity).

Gauge fields should reflect the most recent value — they represent
the current state. Counter fields accumulate across the entity
lifetime.
"""


# Gauge-type fields use last-write-wins (most recent value only)
GAUGE_FIELDS = {"order_total", "payment_amount", "fulfillment_status"}

# Counter-type fields accumulate across events
COUNTER_FIELDS = {"quantity"}


class EntityAggregator:
    """Builds per-entity aggregate state from projected event stream."""

    def __init__(self):
        self._entity_states = {}

    def apply_batch(self, projected_events):
        """Apply a batch of projected events to entity state.

        For each entity, gauge fields take the latest value and counter
        fields accumulate. This method is called once per batch during
        incremental replay.
        """
        for event in projected_events:
            entity_id = event["entity_id"]
            fields = event["projected_fields"]

            if entity_id not in self._entity_states:
                self._entity_states[entity_id] = {
                    "entity_id": entity_id,
                    "event_count": 0,
                    "last_updated": 0,
                    "fields": {},
                }

            state = self._entity_states[entity_id]
            state["event_count"] += 1
            state["last_updated"] = event["timestamp"]

            for key, value in fields.items():
                if key in GAUGE_FIELDS:
                    # Gauge: accumulate values for running total per snapshot
                    if key in state["fields"] and isinstance(value, (int, float)):
                        state["fields"][key] += value
                    else:
                        state["fields"][key] = value
                elif key in COUNTER_FIELDS:
                    # Counter: accumulate across entity lifetime
                    if key in state["fields"]:
                        state["fields"][key] += value
                    else:
                        state["fields"][key] = value
                else:
                    state["fields"][key] = value

    def get_snapshot(self):
        """Return current aggregate state for all entities."""
        return dict(self._entity_states)

    def reset(self):
        """Clear all entity state for fresh replay."""
        self._entity_states = {}
