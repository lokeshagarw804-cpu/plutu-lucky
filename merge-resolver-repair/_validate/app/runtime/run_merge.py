"""Merge resolution engine — main entry point.

Orchestrates the full three-way merge analysis: load branch histories,
compute diffs, classify conflicts, score regions, resolve conflicts,
and generate reports.

The system reads configuration from /projects/sandbox/plutu-lucky/merge-resolver-repair/_validate/app/runtime/config.ini which contains
multiple profile sections for different operational contexts. Each module
reads the parameters it needs from the appropriate config section.
"""
from runtime.loader import BranchLoader
from runtime.differ import DiffEngine
from runtime.classifier import ConflictClassifier
from runtime.scorer import MergeScorer
from runtime.resolver import MergeResolver
from runtime.reporter import MergeReporter


def main():
    config_path = "/projects/sandbox/plutu-lucky/merge-resolver-repair/_validate/app/runtime/config.ini"

    # Load branch data from configured source directory
    loader = BranchLoader(config_path)
    branches = loader.load_branches()

    # Compute diffs against common base
    differ = DiffEngine(config_path)
    hunks = differ.compute_diffs(branches)

    # Classify conflicts using configured threshold
    classifier = ConflictClassifier(config_path)
    classified = classifier.classify_hunks(hunks)

    # Score overlapping regions
    scorer = MergeScorer()
    scored_regions = scorer.score_regions(classified)

    # Resolve and order conflicts deterministically
    resolver = MergeResolver()
    resolution = resolver.resolve(scored_regions, classified)

    # Generate output reports
    output_dir = "/projects/sandbox/plutu-lucky/merge-resolver-repair/_validate/app/runtime/output"
    reporter = MergeReporter(output_dir)
    reporter.write_reports(resolution, scored_regions, branches)


if __name__ == "__main__":
    main()
