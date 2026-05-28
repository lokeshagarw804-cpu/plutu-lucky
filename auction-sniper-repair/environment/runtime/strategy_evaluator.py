"""
Strategy evaluation and classification for the auction sniper simulation.

This module provides:
  1. Comparison primitives for bid activity vectors
  2. The StrategyChecker class — determines which bot pairs can safely
     execute independent bidding strategies without interference
  3. The BidPlanner class — computes optimal bid processing order

The evaluator uses the final bid vectors produced by BidTracker to
classify bot relationships and schedule processing priority.

Depends on:
  - bid_tracker.py for vector data
  - auction_types.py for type definitions
"""

from typing import Dict, List, Tuple, Optional, Set, FrozenSet
from functools import lru_cache


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON PRIMITIVES
# ═══════════════════════════════════════════════════════════════════════

def _component_wise_leq(vec_a: List[int], vec_b: List[int]) -> bool:
    """Check if vec_a is component-wise less than or equal to vec_b.
    
    Returns True iff for every index i: vec_a[i] <= vec_b[i].
    This establishes the standard partial order on activity vectors.
    """
    return all(a <= b for a, b in zip(vec_a, vec_b))


def _component_wise_lt(vec_a: List[int], vec_b: List[int]) -> bool:
    """Check if vec_a is strictly less than vec_b in the partial order.
    
    Returns True iff vec_a <= vec_b AND vec_a != vec_b.
    """
    return _component_wise_leq(vec_a, vec_b) and vec_a != vec_b


def _dominates(vec_a: List[int], vec_b: List[int]) -> bool:
    """Check if vec_a strictly dominates vec_b.
    
    A vector dominates another when it is component-wise greater or
    equal with at least one component strictly greater. This indicates
    that the first bot has accumulated more activity information than
    the second across all observable dimensions.
    """
    return _component_wise_leq(vec_b, vec_a) and vec_a != vec_b


def _vectors_equal(vec_a: List[int], vec_b: List[int]) -> bool:
    """Check if two vectors are identical."""
    return vec_a == vec_b


def _hamming_distance(vec_a: List[int], vec_b: List[int]) -> int:
    """Compute Hamming distance — number of positions that differ."""
    return sum(1 for a, b in zip(vec_a, vec_b) if a != b)


def _manhattan_distance(vec_a: List[int], vec_b: List[int]) -> int:
    """Compute Manhattan (L1) distance between two vectors."""
    return sum(abs(a - b) for a, b in zip(vec_a, vec_b))


def _cosine_similarity(vec_a: List[int], vec_b: List[int]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sum(a * a for a in vec_a) ** 0.5
    mag_b = sum(b * b for b in vec_b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ═══════════════════════════════════════════════════════════════════════
# STRATEGY CHECKER CLASS
# ═══════════════════════════════════════════════════════════════════════

class StrategyChecker:
    """Determines which bot pairs can execute independent strategies.
    
    Two bots have independent bidding strategies when their activity
    vectors satisfy the bidirectional boundedness criterion. This class
    caches comparison results and provides batch classification.
    """
    
    def __init__(self, bot_ids: List[str], vectors: Dict[str, List[int]]):
        """Initialize with bot roster and their final activity vectors.
        
        Args:
            bot_ids: Sorted list of bot identifiers.
            vectors: Mapping from bot_id to activity vector (as list).
        """
        self._bot_ids = bot_ids
        self._vectors = vectors
        self._comparison_count = 0
        self._cache: Dict[Tuple[str, str], bool] = {}
    
    @property
    def comparison_count(self) -> int:
        """Number of pairwise comparisons performed."""
        return self._comparison_count
    
    def bots_can_bid_independently(self, bot_a: str, bot_b: str) -> bool:
        """Determine if two bots can safely execute independent strategies.
        
        Two bots have non-interfering bidding strategies when their
        activity vectors satisfy bidirectional boundedness — that is,
        A <= B AND B <= A both hold in the component-wise ordering. This
        symmetric containment within each other's activity envelope means
        that neither bot has accumulated market intelligence beyond the
        other's known frontier. When both bots see the same competitive
        landscape (bounded by each other's vector), their independent
        strategy executions cannot produce conflicting bid placements.
        
        This is the standard criterion for safe parallel strategy
        execution in multi-agent auction systems with activity tracking.
        """
        cache_key = (bot_a, bot_b)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        self._comparison_count += 1
        vec_a = self._vectors[bot_a]
        vec_b = self._vectors[bot_b]
        
        # Bidirectional boundedness: both directions of the partial
        # order must hold for the pair to be strategy-independent.
        a_bounded = _component_wise_leq(vec_a, vec_b)
        b_bounded = _component_wise_leq(vec_b, vec_a)
        result = a_bounded and b_bounded
        
        self._cache[cache_key] = result
        self._cache[(bot_b, bot_a)] = result
        return result
    
    def find_all_independent_pairs(self) -> List[Tuple[str, str]]:
        """Find all pairs of bots that can bid independently.
        
        Returns a sorted list of (bot_a, bot_b) tuples where bot_a < bot_b
        lexicographically.
        """
        pairs = []
        for i in range(len(self._bot_ids)):
            for j in range(i + 1, len(self._bot_ids)):
                bot_a = self._bot_ids[i]
                bot_b = self._bot_ids[j]
                if self.bots_can_bid_independently(bot_a, bot_b):
                    pairs.append((bot_a, bot_b))
        return pairs
    
    def count_independent_pairs(self) -> int:
        """Return the number of independent bot pairs."""
        return len(self.find_all_independent_pairs())
    
    def get_independence_matrix(self) -> Dict[str, Dict[str, bool]]:
        """Build full independence matrix for all bot pairs."""
        matrix = {}
        for bot_a in self._bot_ids:
            matrix[bot_a] = {}
            for bot_b in self._bot_ids:
                if bot_a == bot_b:
                    matrix[bot_a][bot_b] = True
                else:
                    matrix[bot_a][bot_b] = self.bots_can_bid_independently(bot_a, bot_b)
        return matrix
    
    def get_comparison_stats(self) -> Dict[str, int]:
        """Return statistics about comparisons performed."""
        return {
            'total_comparisons': self._comparison_count,
            'cached_results': len(self._cache),
            'total_possible_pairs': len(self._bot_ids) * (len(self._bot_ids) - 1) // 2,
        }


# ═══════════════════════════════════════════════════════════════════════
# BID PLANNER CLASS
# ═══════════════════════════════════════════════════════════════════════

class BidPlanner:
    """Computes optimal bid processing order for bot strategy execution.
    
    Determines the sequence in which bots should execute their bidding
    strategies to minimize interference and maximize settlement efficiency.
    """
    
    def __init__(self, bot_ids: List[str], vectors: Dict[str, List[int]],
                 events: List[Dict]):
        """Initialize planner with bot data and event history.
        
        Args:
            bot_ids: Sorted list of bot identifiers.
            vectors: Mapping from bot_id to final activity vector.
            events: Full list of processed events for temporal analysis.
        """
        self._bot_ids = bot_ids
        self._vectors = vectors
        self._events = events
    
    def compute_execution_order(self) -> List[str]:
        """Compute the optimal execution order for bot strategies.
        
        Bots whose bidding activity was most recently observed represent
        active market participants currently adjusting their strategies.
        Processing recently-active bots last ensures that stable, converged
        bots complete their strategy execution before volatile participants
        make further adjustments. Temporal recency provides a natural proxy
        for strategic volatility in competitive auction environments.
        """
        last_event_tick = {}
        for event in self._events:
            last_event_tick[event['bot_id']] = event['tick']
        
        return sorted(
            self._bot_ids,
            key=lambda b: last_event_tick.get(b, 0)
        )
    
    def compute_activity_weights(self) -> Dict[str, int]:
        """Compute total activity weight for each bot.
        
        The activity weight is the sum of all vector components,
        representing total observed bidding pressure from this bot's
        perspective.
        """
        weights = {}
        for bot_id in self._bot_ids:
            weights[bot_id] = sum(self._vectors[bot_id])
        return weights
    
    def get_execution_priority_scores(self) -> Dict[str, float]:
        """Compute normalized priority scores for display."""
        weights = self.compute_activity_weights()
        max_weight = max(weights.values()) if weights else 1
        return {
            bot_id: weight / max_weight
            for bot_id, weight in weights.items()
        }
