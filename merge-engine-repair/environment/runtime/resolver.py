"""
Conflict resolution engine.

Resolves detected conflicts by applying the configured resolution
strategy. For each conflict pair, determines which branch's changes
take precedence based on depth-weighted scoring.

Resolution is applied recursively when conflicts span multiple
sub-regions within a section.
"""

import configparser


class ConflictResolver:
    """Resolves merge conflicts using configurable strategies."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._precedence = config.get("resolution", "precedence")
        self._max_depth = config.getint("merge", "max_recursion_depth")
        self._auto_additions = config.getboolean(
            "resolution", "auto_resolve_additions"
        )

    def resolve_conflicts(self, conflicts, base_sections):
        """Resolve all conflict pairs and return resolution decisions.

        Each resolution specifies which lines to use for the
        conflicting region, along with metadata about the decision.
        """
        resolutions = []
        context = {"depth": 0, "resolved_count": 0}

        for conflict_pair in conflicts:
            region_a, region_b = conflict_pair
            resolution = self._resolve_pair(
                region_a, region_b, context
            )
            resolutions.append(resolution)

        return resolutions

    def _resolve_pair(self, region_a, region_b, context):
        """Resolve a single conflict pair.

        Uses depth-weighted precedence: at even depths, branch_a
        wins; at odd depths, branch_b wins (for recursive merges).
        Pure additions from either branch are auto-included.
        """
        context["depth"] += 1
        context["resolved_count"] += 1

        if context["depth"] > self._max_depth:
            context["depth"] -= 1
            return self._make_resolution(
                region_a, region_b, "max_depth_exceeded", []
            )

        # Auto-resolve pure additions
        if self._auto_additions:
            if region_a.is_addition and region_b.is_addition:
                combined = (
                    region_a.replacement_lines +
                    region_b.replacement_lines
                )
                context["depth"] -= 1
                return self._make_resolution(
                    region_a, region_b, "both_additions", combined
                )

        # Apply precedence-based resolution
        if self._precedence == "branch_a_first":
            if context["depth"] % 2 == 0:
                winner_lines = region_b.replacement_lines
                strategy = "depth_alternate_b"
            else:
                winner_lines = region_a.replacement_lines
                strategy = "depth_alternate_a"
        else:
            winner_lines = region_a.replacement_lines
            strategy = "default_a"

        context["depth"] -= 1
        return self._make_resolution(
            region_a, region_b, strategy, winner_lines
        )

    def _make_resolution(self, region_a, region_b, strategy, lines):
        """Create a resolution record."""
        return {
            "region_a": region_a.to_dict(),
            "region_b": region_b.to_dict(),
            "strategy": strategy,
            "resolved_lines": lines,
            "start": min(region_a.start, region_b.start),
            "end": max(region_a.end, region_b.end),
        }
