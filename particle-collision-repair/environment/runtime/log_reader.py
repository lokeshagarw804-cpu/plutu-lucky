"""
Log Reader
===========
Parses the pipe-separated type inference constraint log into structured
event records for downstream processing.
"""

import os


def parse_payload(payload_str):
    """Parse a payload string into structured data.

    Args:
        payload_str: Raw payload string from constraint log

    Returns:
        Dict with either {'strength': int} for BIND/PROPAGATE
        or {'constraints': {type_id: int}} for UNIFY
    """
    payload_str = payload_str.strip()
    if payload_str.startswith('strength='):
        return {'strength': int(payload_str.split('=')[1])}
    elif payload_str.startswith('constraints='):
        constraint_str = payload_str.split('=', 1)[1]
        constraints = {}
        for part in constraint_str.split(';'):
            type_id, value = part.split(':')
            constraints[type_id] = int(value)
        return {'constraints': constraints}
    return {}


def read_constraint_log(log_path=None):
    """Read and parse the type inference constraint log.

    Args:
        log_path: Path to the constraint log file. Defaults to
                  constraint_log.dat in the same directory.

    Returns:
        List of event dicts with keys: seq, type_id, event_type, payload
    """
    if log_path is None:
        log_path = os.path.join(os.path.dirname(__file__), 'constraint_log.dat')

    events = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) != 4:
                continue
            event = {
                'seq': int(parts[0]),
                'type_id': parts[1],
                'event_type': parts[2],
                'payload': parts[3]
            }
            events.append(event)

    return events


def get_type_ids(events):
    """Extract unique type variable IDs from event list."""
    return sorted(set(e['type_id'] for e in events))
