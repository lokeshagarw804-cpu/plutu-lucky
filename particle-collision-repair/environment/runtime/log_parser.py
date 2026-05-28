"""
Collision Log Parser
====================
Parses the arrow-separated collision trace format used by the particle
collision simulator. Each line encodes a single collision event with
sequence number, particle identifier, event type, and event-specific detail.
"""


def parse_collision_log(filepath):
    """Parse a collision log file into a list of event dictionaries.

    Args:
        filepath: Path to the collision_log.dat file

    Returns:
        List of dicts with keys: seq, particle_id, event_type, detail
    """
    events = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            parts = [p.strip() for p in line.split('->')]
            if len(parts) != 4:
                continue
            event = {
                'seq': int(parts[0]),
                'particle_id': parts[1],
                'event_type': parts[2],
                'detail': parts[3]
            }
            events.append(event)
    return events


def parse_detail(detail_str):
    """Parse an event detail string into a dictionary.

    For DRIFT/SCATTER: 'delta_e=N' -> {'delta_e': N}
    For ABSORB: 'neighbor_state=alpha:5;beta:4;...' -> {'neighbor_state': {particle: value}}
    """
    if detail_str.startswith('delta_e='):
        return {'delta_e': int(detail_str.split('=')[1])}
    elif detail_str.startswith('neighbor_state='):
        state_str = detail_str.split('=', 1)[1]
        pairs = state_str.split(';')
        neighbor_state = {}
        for pair in pairs:
            particle, value = pair.split(':')
            neighbor_state[particle] = int(value)
        return {'neighbor_state': neighbor_state}
    return {}
