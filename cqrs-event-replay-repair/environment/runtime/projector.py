"""Event projector — applies events to build materialized view state.

Processes batches of events through fold operations to build aggregate
state. Each batch produces a snapshot that captures the cumulative state
after processing all events in that batch.
"""
import configparser


class EventProjector:
    """Projects events into materialized aggregate state."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._conflict_resolution = self._config.get(
            "projection", "conflict_resolution"
        )

    def project_batches(self, batches):
        """Process event batches and produce per-batch snapshots.

        Each batch is folded into aggregate state. Snapshots track
        the state at each batch boundary for checkpointing.
        """
        snapshots = []
        aggregate_state = {}

        for batch in batches:
            batch_state = self._process_batch(batch, aggregate_state)
            aggregate_state = batch_state
            snapshots.append(self._take_snapshot(batch_state))

        return snapshots

    def _process_batch(self, batch, current_state):
        """Apply events in a single batch to current aggregate state."""
        state = dict(current_state)

        for event in batch:
            stream = event["stream_id"]
            etype = event["type"]
            payload = event["payload"]

            if stream not in state:
                state[stream] = {
                    "event_count": 0,
                    "entities": {},
                    "totals": {},
                }

            state[stream]["event_count"] += 1
            self._apply_event(state[stream], etype, payload)

        return state

    def _apply_event(self, stream_state, event_type, payload):
        """Apply a single event to its stream's state."""
        entities = stream_state["entities"]
        totals = stream_state["totals"]

        if event_type == "OrderCreated":
            oid = payload["order_id"]
            entities[oid] = {
                "status": "created",
                "customer": payload["customer"],
                "total": payload["total"],
            }
            totals["total_order_value"] = totals.get("total_order_value", 0) + payload["total"]
            totals["order_count"] = totals.get("order_count", 0) + 1

        elif event_type == "OrderConfirmed":
            oid = payload["order_id"]
            if oid in entities:
                entities[oid]["status"] = "confirmed"

        elif event_type == "OrderShipped":
            oid = payload["order_id"]
            if oid in entities:
                entities[oid]["status"] = "shipped"
                entities[oid]["tracking"] = payload["tracking"]

        elif event_type == "OrderDelivered":
            oid = payload["order_id"]
            if oid in entities:
                entities[oid]["status"] = "delivered"
                totals["delivered_count"] = totals.get("delivered_count", 0) + 1

        elif event_type == "OrderCancelled":
            oid = payload["order_id"]
            if oid in entities:
                entities[oid]["status"] = "cancelled"
                totals["cancelled_count"] = totals.get("cancelled_count", 0) + 1

        elif event_type == "StockInitialized":
            sku = payload["sku"]
            entities[sku] = {
                "quantity": payload["quantity"],
                "warehouse": payload["warehouse"],
            }
            totals["total_stock"] = totals.get("total_stock", 0) + payload["quantity"]

        elif event_type == "StockReserved":
            sku = payload["sku"]
            if sku in entities:
                entities[sku]["quantity"] -= payload["quantity"]
                totals["total_reserved"] = totals.get("total_reserved", 0) + payload["quantity"]

        elif event_type == "StockReplenished":
            sku = payload["sku"]
            if sku in entities:
                entities[sku]["quantity"] += payload["quantity"]
                totals["total_stock"] = totals.get("total_stock", 0) + payload["quantity"]

        elif event_type == "StockReleased":
            sku = payload["sku"]
            if sku in entities:
                entities[sku]["quantity"] += payload["quantity"]
                totals["total_reserved"] = totals.get("total_reserved", 0) - payload["quantity"]

        elif event_type == "StockDamaged":
            sku = payload["sku"]
            if sku in entities:
                entities[sku]["quantity"] -= payload["quantity"]
                totals["total_damaged"] = totals.get("total_damaged", 0) + payload["quantity"]

        elif event_type == "StockAudited":
            sku = payload["sku"]
            if sku in entities:
                entities[sku]["quantity"] = payload["actual_quantity"]

        elif event_type == "PaymentInitiated":
            pid = payload["payment_id"]
            entities[pid] = {
                "order_id": payload["order_id"],
                "amount": payload["amount"],
                "method": payload["method"],
                "status": "initiated",
            }
            totals["initiated_total"] = totals.get("initiated_total", 0) + payload["amount"]

        elif event_type == "PaymentCaptured":
            pid = payload["payment_id"]
            if pid in entities:
                entities[pid]["status"] = "captured"
                entities[pid]["processor"] = payload["processor"]
                totals["captured_total"] = totals.get("captured_total", 0) + payload["amount"]

        elif event_type == "PaymentRefunded":
            pid = payload["payment_id"]
            if pid in entities:
                entities[pid]["status"] = "refunded"
                totals["refunded_total"] = totals.get("refunded_total", 0) + payload["amount"]

        elif event_type == "PaymentFeeApplied":
            pid = payload["payment_id"]
            if pid in entities:
                entities[pid]["fee"] = payload["fee"]
                totals["total_fees"] = totals.get("total_fees", 0) + payload["fee"]

        elif event_type == "PaymentSettled":
            pid = payload["payment_id"]
            if pid in entities:
                entities[pid]["status"] = "settled"
                entities[pid]["net_amount"] = payload["net_amount"]
                totals["settled_total"] = totals.get("settled_total", 0) + payload["net_amount"]

    def _take_snapshot(self, state):
        """Create a deep copy snapshot of current state."""
        import copy
        return copy.deepcopy(state)
