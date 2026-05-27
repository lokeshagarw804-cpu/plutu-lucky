"""Merge resolution engine — main entry point.

Orchestrates the full three-way merge analysis: load branch histories,
compute diffs, classify conflicts, score regions, resolve conflicts,
and generate reports.
"""
from runtime.loader import BranchLoader
from runtime.differ import DiffEngine
from runtime.classifier import ConflictClassifier
from runtime.scorer import MergeScorer
from runtime.resolver import MergeResolver
from runtime.reporter import MergeReporter


def main():
    config_path = "/app/runtime/config.ini"

    # Load branch data
    loader = BranchLoader(config_path)
    branches = loader.load_branches()

    # Compute diffs against base
    differ = DiffEngine(config_path)
    hunks = differ.compute_diffs(branches)

    # Classify conflicts
    classifier = ConflictClassifier(config_path)
    classified = classifier.classify_hunks(hunks)

    # Score regions
    scorer = MergeScorer()
    scored_regions = scorer.score_regions(classified)

    # Resolve and order conflicts
    resolver = MergeResolver()
    resolution = resolver.resolve(scored_regions, classified)

    # Generate reports
    output_dir = "/app/runtime/output"
    reporter = MergeReporter(output_dir)
    reporter.write_reports(resolution, scored_regions, branches)


if __name__ == "__main__":
    main()
