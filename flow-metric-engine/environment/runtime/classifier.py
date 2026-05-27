"""Packet classifier — assigns packets to size categories.

Classifies each packet based on configured size boundaries into
categories. Boundaries define the upper limit of each category
(exclusive), so a packet with size exactly equal to a boundary
belongs to the lower category.
"""
import configparser


class PacketClassifier:
    """Classifies packets into size-based categories."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_bounds = self._config.get("classification", "boundaries")
        self._boundaries = [int(b) for b in raw_bounds.split(",")]
        raw_cats = self._config.get("classification", "categories")
        self._categories = [c.strip() for c in raw_cats.split(",")]

    def classify_flow(self, flow_data):
        """Classify all packets in a flow by size category.

        Returns list of category labels, one per packet.
        Boundaries are exclusive upper limits for each category.
        """
        packets = flow_data["packets"]
        labels = []
        for pkt in packets:
            size = pkt["size"]
            label = self._categories[-1]  # default to last category
            for i, boundary in enumerate(self._boundaries):
                if size < boundary:
                    label = self._categories[i]
                    break
            labels.append(label)
        return labels
