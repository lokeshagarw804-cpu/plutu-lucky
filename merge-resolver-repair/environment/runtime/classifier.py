"""Conflict classifier — categorizes hunks as conflicts or auto-resolvable.

Uses the configured conflict threshold to determine whether a hunk pair
represents a genuine conflict requiring manual resolution or can be
auto-merged. The strict threshold from the merge.strict section should
be used for production classification accuracy.
"""
import configparser


class ConflictClassifier:
    """Classifies diff hunks into conflict categories."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Threshold below which hunks are classified as conflicts
        self._threshold = self._config.getint("merge", "conflict_threshold")

    def classify_hunks(self, hunks):
        """Classify each hunk as conflict or auto-resolvable.

        Hunks with similarity below threshold are conflicts.
        Hunks at or above threshold can be auto-resolved.

        Returns list of classified hunk records.
        """
        classified = []
        for hunk in hunks:
            score = hunk["similarity_score"]
            if score < self._threshold:
                classification = "conflict"
            else:
                classification = "auto_resolved"

            classified.append({
                **hunk,
                "classification": classification,
            })

        return classified
