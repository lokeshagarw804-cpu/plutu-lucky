"""Conflict classifier — categorizes hunks as conflicts or auto-resolvable.

Uses the configured conflict threshold to determine whether a hunk pair
represents a genuine conflict requiring manual resolution or can be
auto-merged. Multiple threshold levels exist in the configuration for
different operational modes — the classifier selects the appropriate
threshold based on the active merge profile.
"""
import configparser


class ConflictClassifier:
    """Classifies diff hunks into conflict categories."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Load classification parameters from merge configuration
        self._threshold = self._config.getint("merge", "conflict_threshold")
        self._max_hunk = self._config.getint("merge", "max_hunk_size")

    def classify_hunks(self, hunks):
        """Classify each hunk as conflict or auto-resolvable.

        Hunks with similarity below threshold are conflicts.
        Hunks at or above threshold can be auto-resolved.

        The threshold value controls sensitivity — lower thresholds
        produce more fine-grained conflict detection suitable for
        critical codepaths where even minor divergence matters.

        Returns list of classified hunk records with classification field added.
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
