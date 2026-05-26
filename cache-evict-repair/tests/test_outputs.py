"""Tests for multi-tier cache system output correctness."""
import json
import os

STATS_PATH = "/app/runtime/output/cache_stats.json"
SUMMARY_PATH = "/app/runtime/output/summary.json"


def load_stats():
    with open(STATS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_stats_file_exists():
    """Output file cache_stats.json must be created."""
    assert os.path.isfile(STATS_PATH), f"Missing: {STATS_PATH}"


def test_summary_file_exists():
    """Output file summary.json must be created."""
    assert os.path.isfile(SUMMARY_PATH), f"Missing: {SUMMARY_PATH}"


def test_stats_is_list():
    """cache_stats.json must contain a JSON array."""
    stats = load_stats()
    assert isinstance(stats, list), "cache_stats.json must be a list"


def test_stats_entry_fields():
    """Each stat entry must have client, l1_hits, l2_hits, misses, promotions."""
    stats = load_stats()
    assert len(stats) == 3, f"Expected 3 client entries, got {len(stats)}"
    required = {"client", "l1_hits", "l2_hits", "misses", "promotions"}
    for entry in stats:
        missing = required - set(entry.keys())
        assert not missing, f"Entry missing fields: {missing}"


def test_total_requests():
    """System must process exactly 60 total requests."""
    summary = load_summary()
    assert summary["total_requests"] == 60, (
        f"Expected 60 total requests but got {summary['total_requests']}"
    )


def test_overall_hit_rate():
    """Overall hit rate must be 0.6667."""
    summary = load_summary()
    assert abs(summary["overall_hit_rate"] - 0.6667) < 0.001, (
        f"Expected overall_hit_rate=0.6667 but got {summary['overall_hit_rate']}"
    )


def test_l1_hit_rate():
    """L1 hit rate must be 0.2167."""
    summary = load_summary()
    assert abs(summary["l1_hit_rate"] - 0.2167) < 0.001, (
        f"Expected l1_hit_rate=0.2167 but got {summary['l1_hit_rate']}"
    )


def test_promotions_total():
    """Total promotions across all clients must be 6."""
    summary = load_summary()
    assert summary["promotions_total"] == 6, (
        f"Expected promotions_total=6 but got {summary['promotions_total']}"
    )


def test_evictions_total():
    """Total evictions must be 0 (cache never fills beyond capacity with correct policy)."""
    summary = load_summary()
    assert summary["evictions_total"] == 0, (
        f"Expected evictions_total=0 but got {summary['evictions_total']}"
    )


def test_client_alpha_stats():
    """Client alpha: 0 L1 hits, 9 L2 hits, 11 misses, 3 promotions."""
    stats = load_stats()
    alpha = next(e for e in stats if e["client"] == "client_alpha")
    assert alpha["l1_hits"] == 0, f"alpha l1_hits: expected 0, got {alpha['l1_hits']}"
    assert alpha["l2_hits"] == 9, f"alpha l2_hits: expected 9, got {alpha['l2_hits']}"
    assert alpha["misses"] == 11, f"alpha misses: expected 11, got {alpha['misses']}"
    assert alpha["promotions"] == 3, f"alpha promotions: expected 3, got {alpha['promotions']}"


def test_client_beta_stats():
    """Client beta: 6 L1 hits, 6 L2 hits, 8 misses, 2 promotions."""
    stats = load_stats()
    beta = next(e for e in stats if e["client"] == "client_beta")
    assert beta["l1_hits"] == 6, f"beta l1_hits: expected 6, got {beta['l1_hits']}"
    assert beta["l2_hits"] == 6, f"beta l2_hits: expected 6, got {beta['l2_hits']}"
    assert beta["misses"] == 8, f"beta misses: expected 8, got {beta['misses']}"
    assert beta["promotions"] == 2, f"beta promotions: expected 2, got {beta['promotions']}"


def test_client_gamma_stats():
    """Client gamma: 7 L1 hits, 12 L2 hits, 1 miss, 1 promotion."""
    stats = load_stats()
    gamma = next(e for e in stats if e["client"] == "client_gamma")
    assert gamma["l1_hits"] == 7, f"gamma l1_hits: expected 7, got {gamma['l1_hits']}"
    assert gamma["l2_hits"] == 12, f"gamma l2_hits: expected 12, got {gamma['l2_hits']}"
    assert gamma["misses"] == 1, f"gamma misses: expected 1, got {gamma['misses']}"
    assert gamma["promotions"] == 1, f"gamma promotions: expected 1, got {gamma['promotions']}"


def test_client_beta_l1_hits_nonzero():
    """Client beta must have L1 hits (entries promoted by alpha should be hittable)."""
    stats = load_stats()
    beta = next(e for e in stats if e["client"] == "client_beta")
    assert beta["l1_hits"] > 0, (
        "beta has zero L1 hits — promotions from earlier clients should populate L1"
    )


def test_gamma_misses_minimal():
    """Client gamma processes last so most keys already cached — only 1 miss expected."""
    stats = load_stats()
    gamma = next(e for e in stats if e["client"] == "client_gamma")
    assert gamma["misses"] == 1, (
        f"gamma misses: expected 1 (only new key), got {gamma['misses']}"
    )
