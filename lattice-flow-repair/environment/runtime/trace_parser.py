"""Trace parser for lattice flow simulation logs.

Parses the arrow-separated event format used by the pressure
propagation simulator, extracting junction events for replay.
"""


def parse_trace(trace_path):
    """Parse flow trace log into structured event list.
    
    Args:
        trace_path: Path to flow_trace.log file.
        
    Returns:
        List of event dicts with keys: seq, junction_id, event_type, detail
    """
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
                'junction_id': parts[1],
                'event_type': parts[2],
                'detail': parts[3]
            }
            events.append(event)
    return events


def parse_couple_state(detail_str):
    """Parse COUPLE event detail into pressure state dict.
    
    Args:
        detail_str: String like 'peer_state=junc_alpha:8;junc_beta:6;...'
        
    Returns:
        Dict mapping junction_id to pressure value.
    """
    state_part = detail_str.split('=', 1)[1]
    pairs = state_part.split(';')
    state = {}
    for pair in pairs:
        node_id, value = pair.split(':')
        state[node_id.strip()] = int(value.strip())
    return state
