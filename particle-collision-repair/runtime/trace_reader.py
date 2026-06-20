"""
Trace Reader
=============
Parses the arrow-separated lattice signal trace log into structured
event records for downstream processing.
"""

import os


def parse_payload(payload_str):
    """Parse a payload string into structured data.

    Args:
        payload_str: Raw payload string from trace log

    Returns:
        Dict with either {'gain': int} for PULSE/BURST
        or {'depths': {node_id: int}} for RELAY
    """
    payload_str = payload_str.strip()
    if payload_str.startswith('gain='):
        return {'gain': int(payload_str.split('=')[1])}
    elif payload_str.startswith('depths='):
        depth_str = payload_str.split('=', 1)[1]
        depths = {}
        for part in depth_str.split(';'):
            node_id, value = part.split(':')
            depths[node_id] = int(value)
        return {'depths': depths}
    return {}


def read_trace(trace_path=None):
    """Read and parse the signal trace log.

    Args:
        trace_path: Path to the trace log file. Defaults to
                    signal_trace.log in the same directory.

    Returns:
        List of event dicts with keys: seq, node_id, event_type, payload
    """
    if trace_path is None:
        trace_path = os.path.join(os.path.dirname(__file__), 'signal_trace.log')

    events = []
    with open(trace_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            parts = [p.strip() for p in line.split('->')]
            if len(parts) != 4:
                continue
            event = {
                'seq': int(parts[0]),
                'node_id': parts[1],
                'event_type': parts[2],
                'payload': parts[3]
            }
            events.append(event)

    return events


def get_node_ids(events):
    """Extract unique node IDs from event list."""
    return sorted(set(e['node_id'] for e in events))
