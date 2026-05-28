"""Rebase linearization engine -- main entry point.

Orchestrates the full rebase linearization process: load commit histories,
resolve dependencies, detect conflicts, score groups, produce linearized
sequence, and generate reports.

The system reads configuration from /app/runtime/config.ini which contains
multiple profile sections for different operational contexts. Each module
reads the parameters it needs from the appropriate config section.
"""
from runtime.loader import BranchLoader
from runtime.dependency_resolver import DependencyResolver
from runtime.conflict_detector import ConflictDetector
from runtime.priority_scorer import PriorityScorer
from runtime.linearizer import Linearizer
from runtime.reporter import RebaseReporter


def main():
    config_path = "/app/runtime/config.ini"

    # Load commit data from all branches
    loader = BranchLoader(config_path)
    all_commits = loader.load_branches()

    # Resolve dependencies and filter skipped patches
    resolver = DependencyResolver(config_path)
    filtered, groups = resolver.resolve(all_commits)

    # Detect conflicts based on file overlap
    detector = ConflictDetector(config_path)
    conflicts = detector.detect(filtered)

    # Score dependency groups for prioritization
    scorer = PriorityScorer()
    scored_groups = scorer.score_groups(groups)

    # Produce linearized commit sequence
    linearizer = Linearizer(config_path)
    linearized = linearizer.linearize(scored_groups, filtered)

    # Generate output reports
    output_dir = "/app/runtime/output"
    reporter = RebaseReporter(output_dir)
    reporter.write_reports(linearized, conflicts, scored_groups, all_commits)


if __name__ == "__main__":
    main()
