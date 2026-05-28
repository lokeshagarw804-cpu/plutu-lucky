"""
Tests for the auction sniper simulation.

Validates the bid tracking, strategy independence classification,
execution ordering, and report integrity across 14 test cases
organized in 4 tiers:

  Tier 1 (6 tests): Structural checks — always pass
  Tier 2 (2 tests): Unaffected values — always pass  
  Tier 3 (4 tests): Bug-sensitive — require fixes to pass
  Tier 4 (2 tests): Full consistency — require all bugs fixed
"""

import json
import os
import sys
import hashlib

import pytest

# Ensure runtime is importable
sys.path.insert(0, '/app/runtime')


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════

STATE_FILE = '/app/runtime/bid_state.jsonl'
REPORT_FILE = '/app/runtime/strategy_report.json'


@pytest.fixture(scope='session')
def state_records():
    """Load all JSONL state records."""
    records = []
    with open(STATE_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@pytest.fixture(scope='session')
def report():
    """Load the strategy report."""
    with open(REPORT_FILE, 'r') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════
# TIER 1: STRUCTURAL CHECKS (always pass)
# ═══════════════════════════════════════════════════════════════════════

class TestTier1Structural:
    """Basic structural validation — independent of bug presence."""
    
    def test_output_files_exist(self):
        """Both output files must be present after simulation."""
        assert os.path.isfile(STATE_FILE), f"State file missing: {STATE_FILE}"
        assert os.path.isfile(REPORT_FILE), f"Report file missing: {REPORT_FILE}"
    
    def test_bot_count(self, report):
        """Session must contain exactly 7 bots."""
        assert report['session_summary']['total_bots'] == 7
    
    def test_bot_ids(self, report):
        """Bot identifiers must match expected roster."""
        expected = [
            'bot_alpha', 'bot_beta', 'bot_delta', 'bot_epsilon',
            'bot_eta', 'bot_gamma', 'bot_zeta'
        ]
        assert sorted(report['session_summary']['bot_ids']) == expected
    
    def test_events_per_bot(self, state_records):
        """Spot-check event counts for specific bots."""
        counts = {}
        for rec in state_records:
            bid = rec['bot_id']
            counts[bid] = counts.get(bid, 0) + 1
        # bot_alpha has 7 events, bot_delta has 6
        assert counts['bot_alpha'] == 7
        assert counts['bot_delta'] == 6
    
    def test_report_required_fields(self, report):
        """Report must contain all required top-level sections."""
        required = [
            'session_summary', 'activity_vectors',
            'independence_analysis', 'execution_plan', 'integrity'
        ]
        for field in required:
            assert field in report, f"Missing report field: {field}"
    
    def test_total_event_count(self, state_records):
        """Total number of processed events must be 45."""
        assert len(state_records) == 45


# ═══════════════════════════════════════════════════════════════════════
# TIER 2: UNAFFECTED VALUES (always pass)
# ═══════════════════════════════════════════════════════════════════════

class TestTier2Unaffected:
    """Values that remain correct regardless of bug presence."""
    
    def test_epsilon_own_component(self, report):
        """bot_epsilon has no SYNC_INTEL events, so its own component
        is unaffected by Bug 1. With 4 SPOT (+4) and 2 SURGE (+4),
        own = 3 + 4 + 4 = 11."""
        epsilon_own = report['activity_vectors']['bot_epsilon']['own_component']
        assert epsilon_own == 11
    
    def test_total_possible_pairs(self, report):
        """Total possible pairs C(7,2) = 21 — structural constant."""
        assert report['independence_analysis']['total_possible_pairs'] == 21


# ═══════════════════════════════════════════════════════════════════════
# TIER 3: BUG-SENSITIVE (require fixes to pass)
# ═══════════════════════════════════════════════════════════════════════

class TestTier3BugSensitive:
    """Tests that fail when bugs are present."""
    
    def test_alpha_own_component(self, report):
        """bot_alpha has 1 SYNC_INTEL event. With Bug 1 fixed, own
        component should be BASE(3) + 4*SPOT(4) + 2*SURGE(4) + 1*SYNC(1) = 12.
        Buggy code gives 11 (missing the +1 from sync)."""
        alpha_own = report['activity_vectors']['bot_alpha']['own_component']
        assert alpha_own == 12
    
    def test_syncing_bot_weight_vs_non_syncing(self, report):
        """bot_zeta (1 sync) should have weight 32. With Bug 1, it has 31.
        Compare: bot_epsilon (0 syncs) has weight 29 regardless."""
        zeta_weight = report['activity_vectors']['bot_zeta']['total_weight']
        epsilon_weight = report['activity_vectors']['bot_epsilon']['total_weight']
        # Zeta should be higher than epsilon by more than 2
        assert zeta_weight == 32
        assert zeta_weight - epsilon_weight == 3
    
    def test_execution_order_endpoints(self, report):
        """First bot in execution order should be bot_epsilon (lowest weight=29),
        last should be bot_gamma (highest weight=34, stable sort after bot_eta).
        Buggy code sorts by last tick instead."""
        order = report['execution_plan']['order']
        assert order[0] == 'bot_epsilon', f"First should be bot_epsilon, got {order[0]}"
        # Last two should be bot_eta and bot_gamma (both weight 34), 
        # eta comes first alphabetically so gamma is last
        assert order[-1] == 'bot_gamma', f"Last should be bot_gamma, got {order[-1]}"
    
    def test_independent_pair_count(self, report):
        """With Bug 2 fixed (incomparability check), all 21 pairs should
        be independent since no vector dominates another after Bug 1 fix.
        Buggy code (equality check) gives 0 pairs."""
        pair_count = report['independence_analysis']['independent_pair_count']
        assert pair_count == 21


# ═══════════════════════════════════════════════════════════════════════
# TIER 4: FULL CONSISTENCY (require ALL bugs fixed)
# ═══════════════════════════════════════════════════════════════════════

class TestTier4Consistency:
    """Full system integrity — require all bugs to be fixed."""
    
    def test_integrity_digest(self, report):
        """The 16-char hex digest must match expected value computed
        from correct vectors, independence pairs, and execution order."""
        expected_digest = '818b1acf0fc89d5e'
        actual_digest = report['integrity']['digest']
        assert actual_digest == expected_digest, (
            f"Digest mismatch: expected {expected_digest}, got {actual_digest}"
        )
    
    def test_aggregate_own_component_sum(self, report):
        """Sum of all bots' own components must equal 77.
        
        Each bot's own component reflects BASE + local bids + sync
        increments. The aggregate validates that sync events are
        properly counted as local activity contributions.
        Buggy code gives 71 (missing 6 sync increments).
        """
        total_own = sum(
            data['own_component']
            for data in report['activity_vectors'].values()
        )
        assert total_own == 77, (
            f"Aggregate own-component sum: expected 77, got {total_own}"
        )
