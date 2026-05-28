"""
Auction domain type definitions and utility structures.

This module provides the foundational data types used throughout the
auction sniper simulation. It defines bot profiles, lot categories,
bidding strategy enumerations, market condition models, and session
management utilities.

All classes here are imported by bid_tracker.py, strategy_evaluator.py,
and auction_report.py for type annotations and status tracking. The
computation logic itself resides in those downstream modules — this
file is purely declarative and structural.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, FrozenSet
import hashlib
import time


# ═══════════════════════════════════════════════════════════════════════
# ENUMERATIONS
# ═══════════════════════════════════════════════════════════════════════

class BidStrategy(Enum):
    """Enumeration of recognized bidding strategies.
    
    Each bot operates under exactly one strategy profile that governs
    its aggression level, timing preferences, and risk tolerance.
    """
    CONSERVATIVE = auto()
    MODERATE = auto()
    AGGRESSIVE = auto()
    ADAPTIVE = auto()
    SNIPING = auto()
    FRONTRUNNING = auto()


class LotRarity(Enum):
    """Rarity classification for auction lots.
    
    Determines base price multipliers and expected competition levels.
    """
    COMMON = auto()
    UNCOMMON = auto()
    RARE = auto()
    EPIC = auto()
    LEGENDARY = auto()


class MarketPhase(Enum):
    """Current phase of the auction market cycle.
    
    Markets cycle through these phases affecting bid multipliers
    and bot behavior thresholds.
    """
    OPENING = auto()
    ACCUMULATION = auto()
    MARKUP = auto()
    DISTRIBUTION = auto()
    DECLINE = auto()
    RECOVERY = auto()


class SessionStatus(Enum):
    """Status of an auction session."""
    PENDING = auto()
    ACTIVE = auto()
    PAUSED = auto()
    CLOSING = auto()
    SETTLED = auto()
    CANCELLED = auto()


# ═══════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class BotProfile:
    """Complete profile for an auction bot participant.
    
    Stores identity, strategy configuration, budget constraints,
    and historical performance metrics. Used for display and
    reporting purposes — does not influence bid vector computation.
    """
    bot_id: str
    display_name: str
    strategy: BidStrategy
    base_budget: int
    risk_tolerance: float
    max_concurrent_bids: int
    cooldown_ticks: int
    registered_at: float = field(default_factory=time.time)
    
    # Performance tracking
    total_wins: int = 0
    total_losses: int = 0
    total_spent: int = 0
    average_margin: float = 0.0
    
    @property
    def win_rate(self) -> float:
        """Calculate historical win rate."""
        total = self.total_wins + self.total_losses
        if total == 0:
            return 0.0
        return self.total_wins / total
    
    @property
    def remaining_budget(self) -> int:
        """Calculate remaining available budget."""
        return max(0, self.base_budget - self.total_spent)
    
    @property
    def efficiency_score(self) -> float:
        """Compute efficiency as wins per unit spent."""
        if self.total_spent == 0:
            return 0.0
        return self.total_wins / (self.total_spent / 1000.0)
    
    def compute_profile_hash(self) -> str:
        """Generate a deterministic hash of the bot profile configuration."""
        h = hashlib.md5()
        h.update(self.bot_id.encode())
        h.update(self.strategy.name.encode())
        h.update(str(self.base_budget).encode())
        h.update(f"{self.risk_tolerance:.4f}".encode())
        return h.hexdigest()[:12]


@dataclass
class LotDescriptor:
    """Descriptor for an auction lot item.
    
    Contains all metadata needed for valuation and display.
    Does not participate in bid vector logic.
    """
    lot_id: str
    name: str
    rarity: LotRarity
    base_price: int
    category: str
    provenance: str = "unknown"
    condition_score: float = 1.0
    estimated_value: Optional[int] = None
    
    @property
    def rarity_multiplier(self) -> float:
        """Price multiplier based on rarity tier."""
        multipliers = {
            LotRarity.COMMON: 1.0,
            LotRarity.UNCOMMON: 1.5,
            LotRarity.RARE: 2.5,
            LotRarity.EPIC: 4.0,
            LotRarity.LEGENDARY: 7.5,
        }
        return multipliers.get(self.rarity, 1.0)
    
    @property
    def adjusted_value(self) -> int:
        """Compute condition-adjusted estimated value."""
        base = self.estimated_value or self.base_price
        return int(base * self.condition_score * self.rarity_multiplier)
    
    def matches_filter(self, categories: Set[str], min_rarity: LotRarity) -> bool:
        """Check if lot matches search filter criteria."""
        if categories and self.category not in categories:
            return False
        rarity_order = list(LotRarity)
        return rarity_order.index(self.rarity) >= rarity_order.index(min_rarity)


@dataclass
class MarketCondition:
    """Snapshot of market conditions at a point in time.
    
    Tracks volatility, liquidity, and participant density metrics
    that inform strategy adaptation. These values are computed from
    historical bid patterns but do not affect the core vector logic.
    """
    tick: int
    phase: MarketPhase
    volatility_index: float
    liquidity_ratio: float
    active_bot_count: int
    average_bid_gap: float
    price_momentum: float
    
    @property
    def is_favorable(self) -> bool:
        """Determine if conditions favor aggressive bidding."""
        return (
            self.volatility_index < 0.3
            and self.liquidity_ratio > 0.6
            and self.price_momentum > 0.0
        )
    
    @property
    def risk_factor(self) -> float:
        """Compute composite risk factor from market indicators."""
        vol_weight = 0.4
        liq_weight = 0.35
        mom_weight = 0.25
        risk = (
            self.volatility_index * vol_weight
            + (1.0 - self.liquidity_ratio) * liq_weight
            + max(0.0, -self.price_momentum) * mom_weight
        )
        return min(1.0, max(0.0, risk))
    
    def compute_phase_duration_estimate(self, history: List['MarketCondition']) -> int:
        """Estimate remaining ticks in current market phase.
        
        Uses historical phase durations to project when the next
        transition is likely to occur.
        """
        same_phase = [m for m in history if m.phase == self.phase]
        if len(same_phase) < 2:
            return 10  # default estimate
        durations = []
        streak = 1
        for i in range(1, len(same_phase)):
            if same_phase[i].tick - same_phase[i-1].tick <= 2:
                streak += 1
            else:
                durations.append(streak)
                streak = 1
        durations.append(streak)
        avg_duration = sum(durations) / len(durations)
        current_streak = 0
        for m in reversed(history):
            if m.phase == self.phase:
                current_streak += 1
            else:
                break
        return max(1, int(avg_duration - current_streak))


@dataclass
class BidRecord:
    """Record of a single bid placed in the auction.
    
    Immutable after creation. Used for audit trail and
    historical analysis.
    """
    record_id: str
    tick: int
    bot_id: str
    lot_id: str
    amount: int
    bid_type: str
    strategy_at_time: BidStrategy
    market_phase_at_time: MarketPhase
    
    @property
    def is_surge(self) -> bool:
        """Whether this was an aggressive surge bid."""
        return self.bid_type == 'SURGE_BID'
    
    @property
    def premium_ratio(self) -> float:
        """Ratio above base price (requires lot context)."""
        return self.amount / 100.0  # normalized


@dataclass
class SessionConfig:
    """Configuration for an auction session.
    
    Defines duration, participant limits, and settlement rules.
    """
    session_id: str
    max_ticks: int
    max_participants: int
    min_bid_increment: int
    settlement_delay: int
    allow_sniping: bool
    enable_intel_sync: bool
    market_cycle_length: int
    
    # Penalty parameters
    overbid_penalty_rate: float = 0.05
    timeout_penalty: int = 50
    
    def validate(self) -> List[str]:
        """Return list of validation errors, empty if valid."""
        errors = []
        if self.max_ticks < 10:
            errors.append("max_ticks must be >= 10")
        if self.max_participants < 2:
            errors.append("max_participants must be >= 2")
        if self.min_bid_increment < 1:
            errors.append("min_bid_increment must be >= 1")
        if self.settlement_delay < 0:
            errors.append("settlement_delay cannot be negative")
        if self.market_cycle_length < 5:
            errors.append("market_cycle_length must be >= 5")
        return errors
    
    def compute_config_fingerprint(self) -> str:
        """Deterministic fingerprint of session configuration."""
        h = hashlib.sha256()
        h.update(self.session_id.encode())
        h.update(str(self.max_ticks).encode())
        h.update(str(self.max_participants).encode())
        h.update(str(self.min_bid_increment).encode())
        h.update(str(int(self.allow_sniping)).encode())
        h.update(str(int(self.enable_intel_sync)).encode())
        return h.hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def classify_lot_rarity(base_price: int) -> LotRarity:
    """Classify a lot's rarity based on its base price threshold."""
    if base_price >= 500:
        return LotRarity.LEGENDARY
    elif base_price >= 300:
        return LotRarity.EPIC
    elif base_price >= 150:
        return LotRarity.RARE
    elif base_price >= 80:
        return LotRarity.UNCOMMON
    else:
        return LotRarity.COMMON


def determine_market_phase(tick: int, cycle_length: int) -> MarketPhase:
    """Determine market phase based on tick position within cycle."""
    position = tick % cycle_length
    fraction = position / cycle_length
    if fraction < 0.1:
        return MarketPhase.OPENING
    elif fraction < 0.3:
        return MarketPhase.ACCUMULATION
    elif fraction < 0.5:
        return MarketPhase.MARKUP
    elif fraction < 0.7:
        return MarketPhase.DISTRIBUTION
    elif fraction < 0.85:
        return MarketPhase.DECLINE
    else:
        return MarketPhase.RECOVERY


def compute_strategy_compatibility(s1: BidStrategy, s2: BidStrategy) -> float:
    """Compute compatibility score between two strategies.
    
    Returns value in [0, 1] where 1 means strategies never conflict
    and 0 means they always compete for the same lots.
    """
    compatibility_matrix = {
        (BidStrategy.CONSERVATIVE, BidStrategy.AGGRESSIVE): 0.8,
        (BidStrategy.CONSERVATIVE, BidStrategy.SNIPING): 0.7,
        (BidStrategy.MODERATE, BidStrategy.MODERATE): 0.3,
        (BidStrategy.AGGRESSIVE, BidStrategy.AGGRESSIVE): 0.1,
        (BidStrategy.AGGRESSIVE, BidStrategy.FRONTRUNNING): 0.2,
        (BidStrategy.SNIPING, BidStrategy.FRONTRUNNING): 0.9,
        (BidStrategy.ADAPTIVE, BidStrategy.CONSERVATIVE): 0.5,
        (BidStrategy.ADAPTIVE, BidStrategy.AGGRESSIVE): 0.4,
    }
    key = (s1, s2)
    if key in compatibility_matrix:
        return compatibility_matrix[key]
    key_rev = (s2, s1)
    if key_rev in compatibility_matrix:
        return compatibility_matrix[key_rev]
    return 0.5  # default neutral compatibility


def format_currency(amount: int) -> str:
    """Format an integer amount as auction currency string."""
    if amount >= 1000000:
        return f"{amount / 1000000:.2f}M"
    elif amount >= 1000:
        return f"{amount / 1000:.1f}K"
    else:
        return f"{amount}"


def compute_lot_similarity(lot_a: LotDescriptor, lot_b: LotDescriptor) -> float:
    """Compute similarity between two lots for clustering purposes.
    
    Uses category match, rarity distance, and price ratio to produce
    a similarity score in [0, 1].
    """
    score = 0.0
    # Category match
    if lot_a.category == lot_b.category:
        score += 0.4
    # Rarity proximity
    rarity_order = list(LotRarity)
    rarity_dist = abs(
        rarity_order.index(lot_a.rarity) - rarity_order.index(lot_b.rarity)
    )
    score += 0.3 * max(0, 1.0 - rarity_dist / 4.0)
    # Price ratio
    if lot_a.base_price > 0 and lot_b.base_price > 0:
        ratio = min(lot_a.base_price, lot_b.base_price) / max(
            lot_a.base_price, lot_b.base_price
        )
        score += 0.3 * ratio
    return score


# ═══════════════════════════════════════════════════════════════════════
# SESSION STATE TRACKER
# ═══════════════════════════════════════════════════════════════════════

class AuctionSessionTracker:
    """Tracks the lifecycle state of an auction session.
    
    Manages transitions between session phases, validates state
    changes, and maintains an audit log of transitions. This is
    used for reporting and does not affect bid vector computation.
    """
    
    VALID_TRANSITIONS = {
        SessionStatus.PENDING: {SessionStatus.ACTIVE, SessionStatus.CANCELLED},
        SessionStatus.ACTIVE: {SessionStatus.PAUSED, SessionStatus.CLOSING},
        SessionStatus.PAUSED: {SessionStatus.ACTIVE, SessionStatus.CANCELLED},
        SessionStatus.CLOSING: {SessionStatus.SETTLED},
        SessionStatus.SETTLED: set(),
        SessionStatus.CANCELLED: set(),
    }
    
    def __init__(self, config: SessionConfig):
        self._config = config
        self._status = SessionStatus.PENDING
        self._transition_log: List[Tuple[int, SessionStatus, SessionStatus]] = []
        self._tick = 0
    
    @property
    def status(self) -> SessionStatus:
        return self._status
    
    @property
    def is_terminal(self) -> bool:
        return self._status in {SessionStatus.SETTLED, SessionStatus.CANCELLED}
    
    def advance_tick(self):
        """Advance the session clock by one tick."""
        self._tick += 1
        if self._tick >= self._config.max_ticks and self._status == SessionStatus.ACTIVE:
            self._transition_to(SessionStatus.CLOSING)
    
    def _transition_to(self, new_status: SessionStatus):
        """Execute a state transition with validation."""
        valid = self.VALID_TRANSITIONS.get(self._status, set())
        if new_status not in valid:
            raise ValueError(
                f"Invalid transition: {self._status.name} -> {new_status.name}"
            )
        self._transition_log.append((self._tick, self._status, new_status))
        self._status = new_status
    
    def get_transition_history(self) -> List[Tuple[int, str, str]]:
        """Return formatted transition history."""
        return [
            (tick, old.name, new.name)
            for tick, old, new in self._transition_log
        ]
    
    def compute_session_duration(self) -> int:
        """Compute total active ticks (excluding paused time)."""
        active_ticks = 0
        in_active = False
        last_active_start = 0
        for tick, old, new in self._transition_log:
            if new == SessionStatus.ACTIVE:
                in_active = True
                last_active_start = tick
            elif old == SessionStatus.ACTIVE:
                in_active = False
                active_ticks += tick - last_active_start
        if in_active:
            active_ticks += self._tick - last_active_start
        return active_ticks
