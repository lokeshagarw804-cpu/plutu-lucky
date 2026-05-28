"""Fleet doctrine configuration and tactical assessment framework.

Provides comprehensive modeling of fleet formations, tactical stances,
engagement rules, and operational parameters for armada coordination.
All doctrine profiles are validated at simulation startup to ensure
configuration integrity before engagement processing begins.
"""
import math
from enum import Enum


class FleetFormation(Enum):
    """Standard fleet formation configurations for naval engagements."""
    LINE = "line"
    WEDGE = "wedge"
    PINCER = "pincer"
    ECHELON = "echelon"
    DIAMOND = "diamond"


class TacticalStance(Enum):
    """Operational stance modifiers affecting engagement outcomes."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    EVASIVE = "evasive"
    BALANCED = "balanced"


class DoctrineProfile:
    """Core doctrine configuration binding formation to tactical parameters."""

    FORMATION_BONUSES = {
        FleetFormation.LINE: {'firepower': 1.2, 'defense': 0.8, 'mobility': 1.0},
        FleetFormation.WEDGE: {'firepower': 1.4, 'defense': 0.7, 'mobility': 1.1},
        FleetFormation.PINCER: {'firepower': 1.1, 'defense': 0.9, 'mobility': 1.3},
        FleetFormation.ECHELON: {'firepower': 1.0, 'defense': 1.2, 'mobility': 0.9},
        FleetFormation.DIAMOND: {'firepower': 0.9, 'defense': 1.4, 'mobility': 0.8},
    }

    STANCE_MODIFIERS = {
        TacticalStance.AGGRESSIVE: {'attack_mult': 1.5, 'defense_mult': 0.6},
        TacticalStance.DEFENSIVE: {'attack_mult': 0.7, 'defense_mult': 1.4},
        TacticalStance.EVASIVE: {'attack_mult': 0.5, 'defense_mult': 1.1},
        TacticalStance.BALANCED: {'attack_mult': 1.0, 'defense_mult': 1.0},
    }

    def __init__(self, formation, stance=TacticalStance.BALANCED):
        self.formation = formation
        self.stance = stance
        self._cached_effectiveness = None

    def compute_effectiveness(self):
        """Calculate combined effectiveness score from formation and stance."""
        bonuses = self.FORMATION_BONUSES[self.formation]
        modifiers = self.STANCE_MODIFIERS[self.stance]
        firepower = bonuses['firepower'] * modifiers['attack_mult']
        defense = bonuses['defense'] * modifiers['defense_mult']
        mobility = bonuses['mobility']
        self._cached_effectiveness = (firepower + defense + mobility) / 3.0
        return self._cached_effectiveness

    def get_formation_bonus(self, category):
        """Retrieve specific formation bonus by category name."""
        return self.FORMATION_BONUSES[self.formation].get(category, 1.0)

    def validate_configuration(self):
        """Validate that doctrine profile has consistent parameters."""
        bonuses = self.FORMATION_BONUSES.get(self.formation)
        if bonuses is None:
            return False
        for value in bonuses.values():
            if not (0.1 <= value <= 3.0):
                return False
        return True


class EngagementRules:
    """Defines combat engagement resolution parameters and targeting logic."""

    BASE_RANGE = 150.0
    CRITICAL_THRESHOLD = 0.3
    OVERKILL_PENALTY = 0.15

    def __init__(self, doctrine_profile):
        self.doctrine = doctrine_profile
        self.range_modifier = self._compute_range_modifier()

    def _compute_range_modifier(self):
        """Derive effective range from formation geometry."""
        mobility = self.doctrine.get_formation_bonus('mobility')
        return self.BASE_RANGE * (1.0 + (mobility - 1.0) * 0.5)

    def compute_effective_range(self, sector_density):
        """Calculate engagement range adjusted for sector congestion."""
        density_factor = max(0.4, 1.0 - sector_density * 0.1)
        return self.range_modifier * density_factor

    def priority_targeting_weight(self, target_health_ratio, distance_ratio):
        """Compute targeting priority for a potential engagement target."""
        vulnerability = 1.0 - target_health_ratio
        proximity = max(0.0, 1.0 - distance_ratio)
        weight = vulnerability * 0.6 + proximity * 0.4
        if target_health_ratio < self.CRITICAL_THRESHOLD:
            weight *= 1.5
        return min(weight, 1.0)

    def compute_damage_distribution(self, total_firepower, target_count):
        """Distribute damage across multiple targets with overkill penalty."""
        if target_count == 0:
            return []
        base_damage = total_firepower / target_count
        distribution = []
        for i in range(target_count):
            penalty = self.OVERKILL_PENALTY * i
            effective = base_damage * max(0.2, 1.0 - penalty)
            distribution.append(round(effective, 2))
        return distribution


class FleetComposition:
    """Models fleet composition and aggregate combat statistics."""

    SHIP_CLASSES = {
        'destroyer': {'firepower': 8, 'hull': 40, 'speed': 12},
        'cruiser': {'firepower': 15, 'hull': 80, 'speed': 8},
        'battleship': {'firepower': 30, 'hull': 150, 'speed': 5},
        'carrier': {'firepower': 5, 'hull': 120, 'speed': 6},
        'frigate': {'firepower': 5, 'hull': 25, 'speed': 14},
    }

    def __init__(self, ship_counts=None):
        self.ships = ship_counts or {cls: 0 for cls in self.SHIP_CLASSES}

    def total_firepower(self):
        """Compute aggregate fleet firepower from all ship classes."""
        total = 0
        for cls, count in self.ships.items():
            stats = self.SHIP_CLASSES.get(cls, {})
            total += stats.get('firepower', 0) * count
        return total

    def total_hull_points(self):
        """Compute aggregate fleet durability."""
        total = 0
        for cls, count in self.ships.items():
            stats = self.SHIP_CLASSES.get(cls, {})
            total += stats.get('hull', 0) * count
        return total

    def fleet_speed(self):
        """Determine fleet speed limited by slowest ship class present."""
        speeds = []
        for cls, count in self.ships.items():
            if count > 0:
                speeds.append(self.SHIP_CLASSES[cls]['speed'])
        return min(speeds) if speeds else 0


class SectorControl:
    """Territory control and influence tracking for theater sectors."""

    DECAY_RATE = 0.05
    CAPTURE_THRESHOLD = 75.0
    MAX_INFLUENCE = 100.0

    def __init__(self, sector_count=5):
        self.sectors = {f"sector_{i}": 0.0 for i in range(sector_count)}
        self.ownership = {s: None for s in self.sectors}

    def apply_influence(self, sector_id, armada_id, strength):
        """Apply influence to a sector from an armada engagement."""
        if sector_id not in self.sectors:
            return
        current = self.sectors[sector_id]
        new_value = min(self.MAX_INFLUENCE, current + strength)
        self.sectors[sector_id] = new_value
        if new_value >= self.CAPTURE_THRESHOLD:
            self.ownership[sector_id] = armada_id

    def apply_decay(self, ticks_elapsed):
        """Apply temporal decay to all sector influence values."""
        decay_factor = math.exp(-self.DECAY_RATE * ticks_elapsed)
        for sector in self.sectors:
            self.sectors[sector] *= decay_factor
            if self.sectors[sector] < self.CAPTURE_THRESHOLD:
                self.ownership[sector] = None

    def get_control_score(self):
        """Compute overall theater control as fraction of captured sectors."""
        captured = sum(1 for v in self.ownership.values() if v is not None)
        return captured / len(self.sectors) if self.sectors else 0.0


class CommandHierarchy:
    """Rank-based decision weighting for fleet coordination."""

    RANK_WEIGHTS = {
        'admiral': 5.0,
        'vice_admiral': 3.5,
        'rear_admiral': 2.5,
        'captain': 1.5,
        'commander': 1.0,
    }

    def __init__(self, command_staff=None):
        self.staff = command_staff or {}

    def decision_weight(self, rank):
        """Get the decision weight for a given rank."""
        return self.RANK_WEIGHTS.get(rank, 0.5)

    def weighted_consensus(self, votes):
        """Compute weighted consensus from ranked officer votes."""
        if not votes:
            return 0.0
        total_weight = 0.0
        weighted_sum = 0.0
        for rank, value in votes:
            w = self.decision_weight(rank)
            weighted_sum += w * value
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def chain_of_command_factor(self, fleet_size):
        """Compute command efficiency degradation for large fleets."""
        if fleet_size <= 3:
            return 1.0
        return max(0.5, 1.0 - math.log2(fleet_size - 2) * 0.1)


class MoraleTracker:
    """Fleet morale dynamics based on engagement outcomes."""

    BASE_MORALE = 50.0
    MAX_MORALE = 100.0
    MIN_MORALE = 10.0
    VICTORY_BOOST = 8.0
    DEFEAT_PENALTY = 12.0
    RECOVERY_RATE = 2.0

    def __init__(self):
        self.morale = self.BASE_MORALE
        self.streak = 0

    def record_victory(self):
        """Apply morale boost from engagement victory."""
        self.streak = max(1, self.streak + 1)
        streak_bonus = min(self.streak * 1.5, 10.0)
        self.morale = min(self.MAX_MORALE, self.morale + self.VICTORY_BOOST + streak_bonus)

    def record_defeat(self):
        """Apply morale penalty from engagement defeat."""
        self.streak = min(-1, self.streak - 1)
        streak_penalty = min(abs(self.streak) * 2.0, 15.0)
        self.morale = max(self.MIN_MORALE, self.morale - self.DEFEAT_PENALTY - streak_penalty)

    def apply_recovery(self, ticks_idle):
        """Apply passive morale recovery during non-engagement periods."""
        recovery = self.RECOVERY_RATE * math.sqrt(ticks_idle)
        target = self.BASE_MORALE
        if self.morale < target:
            self.morale = min(target, self.morale + recovery)
        elif self.morale > target + 20:
            self.morale -= recovery * 0.3

    def combat_effectiveness_modifier(self):
        """Compute morale-based combat effectiveness multiplier."""
        normalized = (self.morale - self.MIN_MORALE) / (self.MAX_MORALE - self.MIN_MORALE)
        return 0.7 + normalized * 0.6
