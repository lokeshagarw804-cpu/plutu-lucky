"""Window aggregator — computes per-window category distributions.

Slides a window across the packet stream and computes the fraction
of packets in each category within each window position.
"""
import configparser


class WindowAggregator:
    """Computes windowed category distributions for classified flows."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("classification", "window_size")
        self._window_step = self._config.getint("classification", "window_step")
        raw_cats = self._config.get("classification", "categories")
        self._categories = [c.strip() for c in raw_cats.split(",")]

    def aggregate(self, labels, flow_data):
        """Compute per-window category fractions.

        Slides window across the label sequence with configured step size.
        Returns list of window records with category fractions and stats.
        """
        packets = flow_data["packets"]
        n = len(labels)
        windows = []

        pos = 0
        while pos + self._window_size <= n:
            win_labels = labels[pos:pos + self._window_size]
            win_packets = packets[pos:pos + self._window_size]

            # Count per category
            counts = {cat: 0 for cat in self._categories}
            for lbl in win_labels:
                counts[lbl] = counts.get(lbl, 0) + 1

            fractions = {cat: counts[cat] / self._window_size for cat in self._categories}

            # Compute mean latency for this window
            mean_lat = sum(p["latency"] for p in win_packets) / self._window_size

            windows.append({
                "start": pos,
                "fractions": fractions,
                "mean_latency": round(mean_lat, 4),
            })

            pos += self._window_size

        return windows
