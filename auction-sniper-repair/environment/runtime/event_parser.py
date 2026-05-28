"""
Event parser for the auction sniper simulation.

Reads semicolon-separated auction log entries and produces structured
event records for downstream processing. Each line in the log has the
format:

    tick;bot_id;EVENT_TYPE;key1=val1;key2=val2;...

Event types:
  SPOT_BID   — standard bid placed at market rate
  SURGE_BID  — aggressive bid placed at premium multiplier
  SYNC_INTEL — bot synchronizes intelligence from peer bots

This module handles format validation, field extraction, and type
coercion. It does NOT perform any bid vector computation or strategy
analysis — that logic lives in bid_tracker.py and strategy_evaluator.py.
"""

from typing import List, Dict, Any, Optional
import os


# Valid event types recognized by the auction engine
VALID_EVENT_TYPES = frozenset({'SPOT_BID', 'SURGE_BID', 'SYNC_INTEL'})

# Expected minimum fields per line
MIN_FIELDS = 4


def _parse_detail_segment(segment: str) -> Dict[str, str]:
    """Parse a key=value detail segment into a dictionary.
    
    Handles nested semicolons within the peers field for SYNC_INTEL
    events by treating the entire remainder after the third semicolon
    as the detail payload.
    """
    result = {}
    pairs = segment.split(';')
    for pair in pairs:
        if '=' not in pair:
            continue
        key, _, value = pair.partition('=')
        result[key.strip()] = value.strip()
    return result


def _coerce_numeric_fields(details: Dict[str, str]) -> Dict[str, Any]:
    """Attempt numeric coercion on detail values.
    
    Values that look like integers are converted; peer intelligence
    strings (containing colons) are left as-is for the bid tracker
    to parse separately.
    """
    coerced = {}
    for key, val in details.items():
        if ':' in val:
            # Peer intelligence payload — leave as string
            coerced[key] = val
        else:
            try:
                coerced[key] = int(val)
            except ValueError:
                coerced[key] = val
    return coerced


def parse_event_line(line: str, line_number: int) -> Optional[Dict[str, Any]]:
    """Parse a single log line into a structured event record.
    
    Returns None for blank lines or comments (lines starting with #).
    Raises ValueError for malformed lines.
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    
    parts = line.split(';', 3)
    if len(parts) < MIN_FIELDS:
        raise ValueError(
            f"Line {line_number}: expected at least {MIN_FIELDS} fields, "
            f"got {len(parts)}: {line!r}"
        )
    
    tick_str, bot_id, event_type = parts[0], parts[1], parts[2]
    detail_segment = parts[3] if len(parts) > 3 else ""
    
    # Validate tick
    try:
        tick = int(tick_str)
    except ValueError:
        raise ValueError(
            f"Line {line_number}: tick must be integer, got {tick_str!r}"
        )
    
    # Validate event type
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(
            f"Line {line_number}: unknown event type {event_type!r}, "
            f"expected one of {sorted(VALID_EVENT_TYPES)}"
        )
    
    # Parse details
    details = _parse_detail_segment(detail_segment)
    details = _coerce_numeric_fields(details)
    
    return {
        'tick': tick,
        'bot_id': bot_id.strip(),
        'event_type': event_type.strip(),
        'details': details,
        'raw_line': line,
        'line_number': line_number,
    }


def load_auction_log(filepath: str) -> List[Dict[str, Any]]:
    """Load and parse the complete auction log file.
    
    Returns a list of structured event records sorted by tick.
    Raises FileNotFoundError if the log does not exist, or
    ValueError if any line is malformed.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Auction log not found: {filepath}")
    
    events = []
    with open(filepath, 'r') as f:
        for line_number, line in enumerate(f, start=1):
            record = parse_event_line(line, line_number)
            if record is not None:
                events.append(record)
    
    # Ensure chronological ordering
    events.sort(key=lambda e: e['tick'])
    return events


def extract_bot_ids(events: List[Dict[str, Any]]) -> List[str]:
    """Extract the sorted list of unique bot identifiers from parsed events."""
    bot_ids = set()
    for event in events:
        bot_ids.add(event['bot_id'])
    return sorted(bot_ids)


def count_events_by_bot(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count total events per bot."""
    counts = {}
    for event in events:
        bid = event['bot_id']
        counts[bid] = counts.get(bid, 0) + 1
    return counts


def count_events_by_type(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count events grouped by event type."""
    counts = {}
    for event in events:
        etype = event['event_type']
        counts[etype] = counts.get(etype, 0) + 1
    return counts


def parse_peer_intel(intel_string: str) -> Dict[str, int]:
    """Parse a peer intelligence payload string.
    
    Format: "bot_a:val;bot_b:val;..."
    Returns dict mapping bot_id -> integer value.
    """
    result = {}
    if not intel_string:
        return result
    pairs = intel_string.split(';')
    for pair in pairs:
        if ':' not in pair:
            continue
        bot_id, _, val_str = pair.partition(':')
        try:
            result[bot_id.strip()] = int(val_str.strip())
        except ValueError:
            continue
    return result
