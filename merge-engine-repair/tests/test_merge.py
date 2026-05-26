"""Validation tests for merge engine output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
GRAPH_PATH = os.path.join(OUTPUT_DIR, "merge_graph.json")
REPORT_PATH = os.path.join(OUTPUT_DIR, "conflict_report.json")


@pytest.fixture(scope="module")
def graph_data():
    """Load merge graph output."""
    with open(GRAPH_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def report_data():
    """Load conflict report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation — ensures system runs to completion."""

    def test_graph_file_exists(self):
        """Merge graph output must be generated."""
        assert os.path.isfile(GRAPH_PATH), (
            "merge_graph.json not found at /app/runtime/output/"
        )

    def test_report_file_exists(self):
        """Conflict report output must be generated."""
        assert os.path.isfile(REPORT_PATH), (
            "conflict_report.json not found at /app/runtime/output/"
        )

    def test_graph_structure(self, graph_data):
        """Graph output has required top-level fields."""
        assert "total_commits" in graph_data
        assert "branches" in graph_data
        assert "branch_count" in graph_data
        assert "commits" in graph_data
        assert "max_depth" in graph_data
        assert "conflicts_resolved" in graph_data

    def test_report_structure(self, report_data):
        """Report output has required top-level fields."""
        assert "total_conflicts" in report_data
        assert "resolutions" in report_data
        assert "resolution_count" in report_data
        assert "similarity_threshold" in report_data
        assert "chunk_count" in report_data
        assert "total_files_analyzed" in report_data


class TestBranchLoading:
    """Validates that all configured branch strategies are loaded."""

    def test_total_commit_count(self, graph_data):
        """All 26 commits from 3 branches must be in the graph.

        Three branches are active: main (10), feature (8), hotfix (8).
        Check /app/runtime/config.ini active_strategies list and ensure
        all strategy types are being matched correctly during loading.
        """
        assert graph_data["total_commits"] == 26, (
            f"Expected 26 total commits from 3 branches, got "
            f"{graph_data['total_commits']}. Check strategy matching "
            f"in /app/runtime/loader.py against config active_strategies."
        )

    def test_branch_count(self, graph_data):
        """Must include all 3 branches."""
        assert graph_data["branch_count"] == 3, (
            f"Expected 3 branches, got {graph_data['branch_count']}. "
            f"Check active_strategies parsing in /app/runtime/loader.py."
        )

    def test_feature_branch_present(self, graph_data):
        """Feature branch must appear in branches list."""
        assert "feature" in graph_data["branches"], (
            "feature branch missing. Check that the patience strategy "
            "matches active_strategies config in /app/runtime/loader.py."
        )

    def test_all_branches_listed(self, graph_data):
        """All expected branches must be listed."""
        assert "main" in graph_data["branches"]
        assert "hotfix" in graph_data["branches"]
        assert "feature" in graph_data["branches"]


class TestAncestryDepth:
    """Validates commit depth calculation logic."""

    def test_max_depth_value(self, graph_data):
        """Max depth must be 10 (length of longest single branch).

        The depth represents the longest individual branch chain, not
        the sum of all branch lengths. Check accumulation logic in
        /app/runtime/ancestry.py — should use max across branches,
        not sum.
        """
        assert graph_data["max_depth"] == 10, (
            f"Expected max_depth=10 (longest single branch), got "
            f"{graph_data['max_depth']}. Check /app/runtime/ancestry.py "
            f"— depth should be max of branch lengths, not their sum."
        )

    def test_max_depth_not_sum(self, graph_data):
        """Max depth must not equal sum of branch lengths (26)."""
        assert graph_data["max_depth"] != 26, (
            "max_depth equals sum of all commits — this is wrong. "
            "Should be max of individual branch lengths."
        )


class TestConflictResolution:
    """Validates conflict detection and resolution."""

    def test_similarity_threshold(self, report_data):
        """Similarity threshold must be 60 from merge.resolution section.

        The resolver should read from the [merge.resolution] config
        section which has the production threshold, not the [resolution]
        section. Check /app/runtime/resolver.py config section name.
        """
        assert report_data["similarity_threshold"] == 60, (
            f"Expected similarity_threshold=60 from [merge.resolution], "
            f"got {report_data['similarity_threshold']}. Check config "
            f"section in /app/runtime/resolver.py — should read from "
            f"[merge.resolution] not [resolution]."
        )

    def test_total_conflicts(self, report_data):
        """Must detect 24 conflict entries across all branch pairs."""
        assert report_data["total_conflicts"] == 24, (
            f"Expected 24 total conflicts, got {report_data['total_conflicts']}."
        )

    def test_resolution_count(self, report_data):
        """Must produce 11 file resolutions (one per conflicted file)."""
        assert report_data["resolution_count"] == 11, (
            f"Expected 11 resolutions, got {report_data['resolution_count']}."
        )

    def test_total_files_analyzed(self, report_data):
        """Must analyze all 18 unique files across branches."""
        assert report_data["total_files_analyzed"] == 18, (
            f"Expected 18 files, got {report_data['total_files_analyzed']}."
        )


class TestChunking:
    """Validates diff chunking with correct chunk size."""

    def test_chunk_count(self, report_data):
        """Must produce 5 chunks with chunk_size=4.

        With 18 files and chunk_size=4: ceil(18/4) = 5 chunks.
        Check /app/runtime/differ.py chunk boundary calculation
        for off-by-one errors in the step size.
        """
        assert report_data["chunk_count"] == 5, (
            f"Expected 5 chunks (18 files / 4 per chunk), got "
            f"{report_data['chunk_count']}. Check chunk boundary "
            f"calculation in /app/runtime/differ.py — step size "
            f"should be chunk_size, not chunk_size+1."
        )

    def test_chunk_max_size(self, report_data):
        """No chunk should exceed chunk_size of 4 files."""
        for chunk in report_data["chunks"]:
            assert len(chunk["files"]) <= 4, (
                f"Chunk {chunk['chunk_id']} has {len(chunk['files'])} files, "
                f"exceeding chunk_size=4."
            )

    def test_last_chunk_has_remainder(self, report_data):
        """Last chunk should have 2 files (18 mod 4 = 2)."""
        chunks = report_data["chunks"]
        last_chunk = chunks[-1]
        assert len(last_chunk["files"]) == 2, (
            f"Last chunk should have 2 files (18 mod 4), "
            f"got {len(last_chunk['files'])}."
        )


class TestCommitOrdering:
    """Validates deterministic commit ordering in merged graph."""

    def test_chronological_order(self, graph_data):
        """Commits must be sorted by timestamp ascending."""
        commits = graph_data["commits"]
        for i in range(1, len(commits)):
            assert commits[i]["timestamp"] >= commits[i - 1]["timestamp"]

    def test_tiebreaker_at_timestamp_500(self, graph_data):
        """Commits at timestamp 1700000500 must be ordered by branch_id.

        Three commits share timestamp 1700000500 (feature, hotfix, main).
        When timestamps are equal, ordering must be deterministic using
        branch_id alphabetically then seq. Check sort key in
        /app/runtime/graph_builder.py — seq alone is not sufficient
        since seq is local to each branch.
        """
        commits = graph_data["commits"]
        ts500 = [c for c in commits if c["timestamp"] == 1700000500]
        assert len(ts500) == 3, (
            f"Expected 3 commits at timestamp 1700000500, got {len(ts500)}. "
            f"All 3 branches must be loaded first."
        )
        branch_order = [c["branch_id"] for c in ts500]
        assert branch_order == ["feature", "hotfix", "main"], (
            f"Commits at ts=1700000500 should be ordered by branch_id: "
            f"feature, hotfix, main. Got {branch_order}. Check sort key "
            f"in /app/runtime/graph_builder.py — must include branch_id."
        )
