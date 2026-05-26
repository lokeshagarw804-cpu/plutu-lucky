"""Event projector. Builds aggregate state from ordered event stream."""
import configparser


class EventProjector:
    """Projects events into aggregate order state using configurable batch sizes."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._batch_size = self._config.getint("projection", "batch_size")

    def project(self, ordered_events):
        """Build aggregate state by replaying events in batches.

        Each batch produces a snapshot of order aggregates. The final
        aggregate state should reflect only the last batch snapshot values.
        """
        aggregates = {}
        batch_count = 0

        for i in range(0, len(ordered_events), self._batch_size):
            batch = ordered_events[i:i + self._batch_size]
            batch_count += 1
            snapshot = self._process_batch(batch)

            for order_id, state in snapshot.items():
                if order_id not in aggregates:
                    aggregates[order_id] = {
                        "order_id": order_id,
                        "customer": None,
                        "items": [],
                        "total_amount": 0.0,
                        "payment_amount": 0.0,
                        "refund_amount": 0.0,
                        "status": "pending",
                        "event_count": 0
                    }
                agg = aggregates[order_id]
                for key in ["total_amount", "payment_amount", "refund_amount", "event_count"]:
                    if key in state:
                        agg[key] += state[key]
                if state.get("customer"):
                    agg["customer"] = state["customer"]
                if state.get("items"):
                    agg["items"] = state["items"]
                if state.get("status"):
                    agg["status"] = state["status"]

        return aggregates

    def _process_batch(self, batch):
        """Process a single batch of events into per-order snapshot."""
        snapshot = {}

        for event in batch:
            etype = event["type"]
            payload = event["payload"]
            order_id = payload.get("order_id")
            if not order_id:
                continue

            if order_id not in snapshot:
                snapshot[order_id] = {
                    "total_amount": 0.0,
                    "payment_amount": 0.0,
                    "refund_amount": 0.0,
                    "event_count": 0,
                    "customer": None,
                    "items": [],
                    "status": None
                }

            state = snapshot[order_id]
            state["event_count"] += 1

            if etype == "OrderCreated":
                state["customer"] = payload["customer"]
                state["items"] = payload["items"]
                item_total = sum(i["qty"] * i["price"] for i in payload["items"])
                state["total_amount"] = item_total
                state["status"] = "created"

            elif etype == "OrderConfirmed":
                state["status"] = "confirmed"

            elif etype == "PaymentReceived":
                state["payment_amount"] = payload["amount"]
                state["status"] = "paid"

            elif etype == "RefundIssued":
                state["refund_amount"] += payload["amount"]
                state["status"] = "partially_refunded"

        return snapshot
