"""Engagement log parser for armada clash simulation.

Reads the pipe-delimited engagement records and produces structured
event data for the vector engine to process.
"""
import os


def parse_engagements(filepath=None):
    """Parse engagement log file into structured event records.

    Args:
        filepath: Optional path to engagements.dat file. Defaults to
                  the file located alongside this module.

    Returns:
        List of event dictionaries with keys: tick, armada_id,
        event_type, target_armada, sector.
    """
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'engagements.dat')
    events = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|')
            events.append({
                'tick': int(parts[0]),
                'armada_id': parts[1],
                'event_type': parts[2],
                'target_armada': parts[3] if parts[3] != 'NONE' else None,
                'sector': parts[4]
            })
    return events
