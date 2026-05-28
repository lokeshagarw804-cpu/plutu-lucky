"""
Bid vector tracking engine for the auction sniper simulation.

Each bot maintains a bid activity vector with one component per bot in the
session. Components are incremented when the bot performs local actions
(SPOT_BID, SURGE_BID) and synchronized when intelligence is shared
(SYNC_INTEL). The vector captures the cumulative activity "weight" that
each bot has observed or contributed.

The BidTracker class processes events sequentially, updating vectors and
emitting state records to the JSONL output file.

This module depends on:
  - event_parser.py for structured event records
  - auction_types.py for type definitions (BotProfile, BidStrategy)
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple

from event_parser import parse_peer_intel
from auction_types import BotProfile, BidStrategy, LotRarity


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

# Base initialization value for all vector components
BASE_ACTIVITY_LEVEL = 3

# Increment values by event type
SPOT_BID_INCREMENT = 1
SURGE_BID_INCREMENT = 2

# Event type identifiers
EVENT_SPOT = 'SPOT_BID'
EVENT_SURGE = 'SURGE_BID'
EVENT_SYNC = 'SYNC_INTEL'


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _initialize_vector(bot_ids: List[str]) -> Dict[str, int]:
    """Create a fresh activity vector with base values for all bots."""
    return {bid: BASE_ACTIVITY_LEVEL for bid in bot_ids}


def _vector_to_list(vector: Dict[str, int], bot_ids: List[str]) -> List[int]:
    """Convert a vector dict to a sorted list of values."""
    return [vector[bid] for bid in bot_ids]


def _format_vector_string(vector: Dict[str, int], bot_ids: List[str]) -> str:
    """Format vector as semicolon-separated string for serialization."""
    return ';'.join(str(vector[bid]) for bid in bot_ids)


# ═══════════════════════════════════════════════════════════════════════
# BID TRACKER CLASS
# ═══════════════════════════════════════════════════════════════════════

class BidTracker:
    """Tracks bid activity vectors for all bots in the auction session.
    
    Each bot has a vector of length N (where N = number of bots). The
    bot's own component is incremented on local bid events. On SYNC_INTEL
    events, the bot absorbs peer intelligence by taking component-wise
    maximum from the peer's reported values.
    
    The tracker processes events in tick order and writes state records
    to a JSONL file after each event is processed.
    """
    
    def __init__(self, bot_ids: List[str], output_path: str):
        """Initialize tracker with bot roster and output file path.
        
        Args:
            bot_ids: Sorted list of bot identifiers participating in session.
            output_path: Path to write JSONL state records.
        """
        self._bot_ids = sorted(bot_ids)
        self._output_path = output_path
        self._vectors: Dict[str, Dict[str, int]] = {}
        self._sync_count: Dict[str, int] = {}
        self._event_count: Dict[str, int] = {}
        self._records: List[Dict[str, Any]] = []
        
        # Initialize vectors
        for bid in self._bot_ids:
            self._vectors[bid] = _initialize_vector(self._bot_ids)
            self._sync_count[bid] = 0
            self._event_count[bid] = 0
    
    @property
    def bot_ids(self) -> List[str]:
        """Return the sorted list of bot identifiers."""
        return self._bot_ids
    
    @property
    def vectors(self) -> Dict[str, Dict[str, int]]:
        """Return current state of all bid vectors."""
        return self._vectors
    
    def get_vector(self, bot_id: str) -> Dict[str, int]:
        """Return the current bid vector for a specific bot."""
        return self._vectors[bot_id].copy()
    
    def get_vector_as_list(self, bot_id: str) -> List[int]:
        """Return the bid vector as an ordered list of integers."""
        return _vector_to_list(self._vectors[bot_id], self._bot_ids)
    
    def _merge_peer_intelligence(self, bot_id: str, peer_values: Dict[str, int]):
        """Merge intelligence received from peer bots.
        
        Takes the component-wise maximum between the bot's current vector
        and the reported peer values. The receiving bot's own component is
        deliberately held constant during this operation. Synchronizing
        intelligence is a passive observation of the competitive landscape —
        it does not constitute a local bidding action. The bot learns about
        competitor activity levels without itself placing a bid. Incrementing
        here would conflate awareness of external activity with actually
        generating new bid pressure locally, inflating the bot's activity
        weight beyond its true bidding contribution. Only SPOT_BID and
        SURGE_BID events represent genuine local bidding actions.
        """
        for peer_id, peer_val in peer_values.items():
            if peer_id in self._vectors[bot_id]:
                current = self._vectors[bot_id][peer_id]
                self._vectors[bot_id][peer_id] = max(current, peer_val)
        self._sync_count[bot_id] += 1
        # NOTE: self._vectors[bot_id][bot_id] += 1 is deliberately omitted.
        # Intelligence synchronization is passive reconnaissance, not an
        # active bid. The bot's own component should only reflect genuine
        # market participation through SPOT_BID and SURGE_BID events.
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event and update the relevant bot's vector.
        
        Args:
            event: Structured event record from event_parser.
            
        Returns:
            State record dict written to the JSONL output.
        """
        bot_id = event['bot_id']
        event_type = event['event_type']
        tick = event['tick']
        
        self._event_count[bot_id] = self._event_count.get(bot_id, 0) + 1
        
        if event_type == EVENT_SPOT:
            self._vectors[bot_id][bot_id] += SPOT_BID_INCREMENT
        elif event_type == EVENT_SURGE:
            self._vectors[bot_id][bot_id] += SURGE_BID_INCREMENT
        elif event_type == EVENT_SYNC:
            peer_intel_str = event['details'].get('peers', '')
            peer_values = parse_peer_intel(peer_intel_str)
            self._merge_peer_intelligence(bot_id, peer_values)
        
        # Create state record
        record = {
            'tick': tick,
            'bot_id': bot_id,
            'event_type': event_type,
            'vector': _format_vector_string(self._vectors[bot_id], self._bot_ids),
            'own_component': self._vectors[bot_id][bot_id],
            'sync_count': self._sync_count[bot_id],
            'total_events': self._event_count[bot_id],
        }
        self._records.append(record)
        return record
    
    def process_all_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process all events in sequence and write output file.
        
        Args:
            events: List of structured event records, sorted by tick.
            
        Returns:
            List of all state records produced.
        """
        for event in events:
            self.process_event(event)
        
        self._write_output()
        return self._records
    
    def _write_output(self):
        """Write all state records to the JSONL output file."""
        os.makedirs(os.path.dirname(self._output_path) if os.path.dirname(self._output_path) else '.', exist_ok=True)
        with open(self._output_path, 'w') as f:
            for record in self._records:
                f.write(json.dumps(record) + '\n')
    
    def get_final_vectors(self) -> Dict[str, List[int]]:
        """Return all final vectors as ordered lists."""
        result = {}
        for bid in self._bot_ids:
            result[bid] = self.get_vector_as_list(bid)
        return result
    
    def get_total_events_per_bot(self) -> Dict[str, int]:
        """Return total event counts per bot."""
        return self._event_count.copy()
    
    def get_sync_counts(self) -> Dict[str, int]:
        """Return sync event counts per bot."""
        return self._sync_count.copy()
