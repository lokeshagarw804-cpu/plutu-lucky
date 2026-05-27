"""Diff engine — computes line-level differences between branch edits.

Produces hunk-level diff records by comparing each branch's edits
against the base version. Each hunk carries a similarity score that
downstream modules use for conflict classification.

Strategy validation ensures only configured strategies are applied;
unrecognized strategies fall back to the default. The strategy set
is loaded from the [strategies] section at initialization time.
"""
import configparser


class DiffEngine:
    """Computes structured diffs between branch edit histories."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_strategies = self._config.get("strategies", "merge_strategies")
        self._strategies = set(raw_strategies.split(","))
        self._default = self._config.get("strategies", "default_strategy")
        self._fallback = self._config.get("strategies", "fallback_strategy")

    def compute_diffs(self, branches):
        """Compute pairwise diffs between all branches and their common base.

        Returns list of hunk records with diff metadata and similarity scores.
        Branch ordering is determined by lexicographic sort of branch IDs,
        with the first entry serving as the common ancestor (base).
        """
        branch_ids = sorted(branches.keys())
        if len(branch_ids) < 2:
            return []

        base_id = branch_ids[0]
        base_edits = branches[base_id]["edits"]

        all_hunks = []
        for bid in branch_ids[1:]:
            branch_edits = branches[bid]["edits"]
            hunks = self._diff_against_base(base_edits, branch_edits, bid)
            all_hunks.extend(hunks)

        return all_hunks

    def _diff_against_base(self, base_edits, branch_edits, branch_id):
        """Compute hunks representing changes from base to branch.

        Uses the configured strategy to determine hunk boundaries.
        Falls back to default if the requested strategy is not available
        in the configured strategy set.
        """
        hunks = []
        hunk_id = 0

        for edit in branch_edits:
            strategy = edit.get("strategy", self._default)
            if strategy not in self._strategies:
                strategy = self._default

            base_match = self._find_base_match(base_edits, edit)
            score = self._compute_similarity(base_match, edit)

            hunks.append({
                "hunk_id": hunk_id,
                "branch_id": branch_id,
                "line_start": edit["line_start"],
                "line_end": edit["line_end"],
                "content": edit["content"],
                "base_content": base_match["content"] if base_match else "",
                "similarity_score": score,
                "strategy": strategy,
            })
            hunk_id += 1

        return hunks

    def _find_base_match(self, base_edits, edit):
        """Find the base edit that covers the same line range.

        Searches for containing match first (base fully covers edit range),
        then falls back to partial overlap (shared start or end line).
        """
        for base_edit in base_edits:
            if (base_edit["line_start"] <= edit["line_start"] and
                    base_edit["line_end"] >= edit["line_end"]):
                return base_edit
            if (base_edit["line_start"] == edit["line_start"] or
                    base_edit["line_end"] == edit["line_end"]):
                return base_edit
        return None

    def _compute_similarity(self, base_match, edit):
        """Compute similarity score between base and branch content.

        Score ranges from 0 (completely different) to 100 (identical).
        Uses line-level comparison with the longer content as denominator.
        """
        if base_match is None:
            return 0

        base_lines = base_match["content"].split("\n")
        edit_lines = edit["content"].split("\n")

        if not base_lines or not edit_lines:
            return 0

        matching = sum(1 for a, b in zip(base_lines, edit_lines) if a == b)
        total = max(len(base_lines), len(edit_lines))

        return int((matching / total) * 100) if total > 0 else 0
