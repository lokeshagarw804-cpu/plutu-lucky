"""Materializer. Produces final output files from projected aggregates."""
import json
import os
import configparser


class Materializer:
    """Writes aggregate summaries and event timeline to output directory."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._output_dir = self._config.get("output", "directory")
        self._summary_file = self._config.get("output", "summary_file")
        self._timeline_file = self._config.get("output", "timeline_file")

    def materialize(self, aggregates, timeline):
        """Write output files."""
        os.makedirs(self._output_dir, exist_ok=True)

        summary = self._build_summary(aggregates)
        summary_path = os.path.join(self._output_dir, self._summary_file)
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        timeline_output = self._build_timeline(timeline)
        timeline_path = os.path.join(self._output_dir, self._timeline_file)
        with open(timeline_path, "w") as f:
            json.dump(timeline_output, f, indent=2)

    def _build_summary(self, aggregates):
        """Build the aggregate summary document."""
        orders = []
        for order_id in sorted(aggregates.keys()):
            agg = aggregates[order_id]
            net_revenue = agg["payment_amount"] - agg["refund_amount"]
            orders.append({
                "order_id": agg["order_id"],
                "customer": agg["customer"],
                "item_count": len(agg["items"]),
                "total_amount": agg["total_amount"],
                "payment_amount": agg["payment_amount"],
                "refund_amount": agg["refund_amount"],
                "net_revenue": net_revenue,
                "status": agg["status"],
                "event_count": agg["event_count"]
            })

        total_revenue = sum(o["net_revenue"] for o in orders)
        total_orders = len(orders)
        total_events = sum(o["event_count"] for o in orders)

        return {
            "generated_at": "2024-03-01T16:00:00Z",
            "total_orders": total_orders,
            "total_events_processed": total_events,
            "total_net_revenue": round(total_revenue, 2),
            "orders": orders
        }

    def _build_timeline(self, events):
        """Build the event timeline document."""
        entries = []
        for idx, event in enumerate(events):
            entries.append({
                "position": idx + 1,
                "event_id": event["event_id"],
                "stream_id": event["stream_id"],
                "timestamp": event["timestamp"],
                "type": event["type"],
                "order_id": event["payload"].get("order_id")
            })

        return {
            "total_events": len(entries),
            "entries": entries
        }
