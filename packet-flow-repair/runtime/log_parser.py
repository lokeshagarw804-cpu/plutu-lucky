"""Log parser for network intrusion detection capture logs.

Parses the arrow-separated event format used by the distributed
sensor network, extracting detection events for replay.
"""


def parse_log(log_path):
    """Parse capture log into structured event list.
    
    Args:
        log_path: Path to capture_log.dat file.
        
    Returns:
        List of event dicts with keys: seq, sensor_id, event_type, detail
    """
    events = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            parts = [p.strip() for p in line.split('->')]
            if len(parts) != 4:
                continue
            event = {
                'seq': int(parts[0]),
                'sensor_id': parts[1],
                'event_type': parts[2],
                'detail': parts[3]
            }
            events.append(event)
    return events


def parse_sync_state(detail_str):
    """Parse SYNC event detail into observation state dict.
    
    Args:
        detail_str: String like 'peer_state=sensor_north:8;sensor_south:6;...'
        
    Returns:
        Dict mapping sensor_id to observation value.
    """
    state_part = detail_str.split('=', 1)[1]
    pairs = state_part.split(';')
    state = {}
    for pair in pairs:
        node_id, value = pair.split(':')
        state[node_id.strip()] = int(value.strip())
    return state
