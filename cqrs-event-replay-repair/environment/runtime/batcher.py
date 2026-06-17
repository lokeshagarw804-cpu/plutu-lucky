"""Event batcher — splits sequenced events into processing batches.

Batches are sized according to the replay configuration to control
memory usage and checkpoint frequency during event replay.
"""
import configparser


class EventBatcher:
    """Splits a sequenced event list into fixed-size batches."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._batch_size = self._config.getint("replay", "batch_size")

    def create_batches(self, events):
        """Split events into batches of configured size.

        Returns list of batch lists. Each batch contains up to
        batch_size events in their sequenced order.
        """
        batches = []
        for i in range(0, len(events), self._batch_size):
            batch = events[i:i + self._batch_size]
            batches.append(batch)
        return batches
