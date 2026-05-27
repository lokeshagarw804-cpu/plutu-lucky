"""Traffic matrix builder — assembles interface flow statistics.

Builds a summary matrix ordering interfaces by identifier and
computing aggregate statistics for cross-interface comparison.
"""


class TrafficMatrix:
    """Builds the interface traffic summary matrix."""

    def build(self, interfaces, bw_results, lat_results):
        """Construct traffic matrix from per-interface metrics.

        Interfaces are sorted by identifier for consistent ordering.
        Returns dict with interface_order and per-interface summaries.
        """
        interface_ids = sorted(interfaces.keys())

        summaries = []
        for iface_id in interface_ids:
            bw = bw_results[iface_id]
            lat = lat_results[iface_id]

            avg_bw = sum(w["bandwidth_bps"] for w in bw) / len(bw) if bw else 0
            max_bw = max(w["bandwidth_bps"] for w in bw) if bw else 0
            avg_lat = sum(w["mean_latency"] for w in lat) / len(lat) if lat else 0
            avg_jitter = sum(w["jitter"] for w in lat) / len(lat) if lat else 0
            p95_lat = sum(w["percentile_value"] for w in lat) / len(lat) if lat else 0

            summaries.append({
                "interface_id": iface_id,
                "avg_bandwidth_bps": round(avg_bw, 4),
                "max_bandwidth_bps": round(max_bw, 4),
                "avg_latency_ms": round(avg_lat, 4),
                "avg_jitter_ms": round(avg_jitter, 4),
                "p95_latency_ms": round(p95_lat, 4),
            })

        return {
            "interface_order": interface_ids,
            "count": len(interface_ids),
            "summaries": summaries,
        }
