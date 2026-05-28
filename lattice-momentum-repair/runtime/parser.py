"""Lattice Boltzmann propagation log parser.

Parses the arrow-separated event log format, extracting structured
event records for downstream momentum computation.
"""


def parse_log(log_path):
    """Parse propagation log file and return list of event dicts.

    Each event dict has: seq, cell_id, event_type, detail
    For COLLISION events, detail is parsed into a dict of cell_id -> int values.
    For STREAM/DRIFT events, detail is parsed into delta (int).
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
            seq = int(parts[0])
            cell_id = parts[1]
            event_type = parts[2]
            raw_detail = parts[3]

            if event_type == 'COLLISION':
                # Parse neighbor_state=cell_alpha:8;cell_beta:6;...
                state_str = raw_detail.split('=', 1)[1]
                neighbor_state = {}
                for pair in state_str.split(';'):
                    k, v = pair.split(':')
                    neighbor_state[k.strip()] = int(v.strip())
                detail = neighbor_state
            else:
                # Parse delta=N
                delta = int(raw_detail.split('=')[1])
                detail = delta

            events.append({
                'seq': seq,
                'cell_id': cell_id,
                'event_type': event_type,
                'detail': detail
            })
    return events
