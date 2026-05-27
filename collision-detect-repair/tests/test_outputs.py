"""Tests for particle collision detection system output correctness."""
import json
import os

COLLISIONS_PATH = "/app/runtime/output/collisions.json"
SUMMARY_PATH = "/app/runtime/output/summary.json"


def load_collisions():
    with open(COLLISIONS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_collisions_file_exists():
    """Output file collisions.json must be created."""
    assert os.path.isfile(COLLISIONS_PATH), f"Missing: {COLLISIONS_PATH}"


def test_summary_file_exists():
    """Output file summary.json must be created."""
    assert os.path.isfile(SUMMARY_PATH), f"Missing: {SUMMARY_PATH}"


def test_collisions_is_list():
    """collisions.json must contain a JSON array."""
    data = load_collisions()
    assert isinstance(data, list), "collisions.json must be a list"


def test_collision_entry_fields():
    """Each collision entry must have pair, cell, response_velocity, restitution."""
    data = load_collisions()
    assert len(data) > 0, "collisions.json must not be empty"
    required = {"pair", "cell", "response_velocity", "restitution"}
    for entry in data[:5]:
        missing = required - set(entry.keys())
        assert not missing, f"Entry missing fields: {missing}"


def test_total_collisions():
    """Summary total_collisions must be 123 (all interactions across both frames)."""
    summary = load_summary()
    assert summary["total_collisions"] == 123, (
        f"Expected total_collisions=123 but got {summary['total_collisions']}"
    )


def test_unique_pairs():
    """Summary unique_pairs must be 63."""
    summary = load_summary()
    assert summary["unique_pairs"] == 63, (
        f"Expected unique_pairs=63 but got {summary['unique_pairs']}"
    )


def test_avg_response_velocity():
    """Average response velocity must be 1.254651."""
    summary = load_summary()
    assert abs(summary["avg_response_velocity"] - 1.254651) < 0.0001, (
        f"Expected avg_response_velocity=1.254651 but got "
        f"{summary['avg_response_velocity']}"
    )


def test_max_response_velocity():
    """Maximum response velocity must be 3.603748."""
    summary = load_summary()
    assert abs(summary["max_response_velocity"] - 3.603748) < 0.0001, (
        f"Expected max_response_velocity=3.603748 but got "
        f"{summary['max_response_velocity']}"
    )


def test_cells_with_collisions():
    """Number of distinct cells with collisions must be 21."""
    summary = load_summary()
    assert summary["cells_with_collisions"] == 21, (
        f"Expected cells_with_collisions=21 but got "
        f"{summary['cells_with_collisions']}"
    )


def test_restitution_value():
    """All collision entries must use restitution coefficient 0.6."""
    data = load_collisions()
    for entry in data:
        assert abs(entry["restitution"] - 0.6) < 0.001, (
            f"Expected restitution=0.6 but got {entry['restitution']} "
            f"for pair {entry['pair']}"
        )


def test_collisions_list_length():
    """The collisions.json list must contain exactly 123 entries."""
    data = load_collisions()
    assert len(data) == 123, (
        f"Expected 123 collision entries but got {len(data)}"
    )


def test_multi_frame_pairs_exist():
    """At least 50 unique pairs must have interactions in both frames."""
    data = load_collisions()
    pair_counts = {}
    for entry in data:
        key = tuple(entry["pair"])
        pair_counts[key] = pair_counts.get(key, 0) + 1
    multi = sum(1 for v in pair_counts.values() if v >= 2)
    assert multi >= 50, (
        f"Expected at least 50 pairs with multi-frame interactions, got {multi}"
    )


def test_negative_coord_cells():
    """Collisions must include cells with negative indices (particles at negative coords)."""
    data = load_collisions()
    neg_cells = set()
    for entry in data:
        cell = tuple(entry["cell"])
        if cell[0] < 0 or cell[1] < 0:
            neg_cells.add(cell)
    assert len(neg_cells) >= 5, (
        f"Expected at least 5 distinct negative-index cells, got {len(neg_cells)}: "
        f"{neg_cells}"
    )


def test_specific_pair_velocity():
    """The L01-L02 pair must have max response velocity of 3.603748."""
    data = load_collisions()
    l01_l02 = [e for e in data if e["pair"] == ["L01", "L02"]]
    assert len(l01_l02) == 2, (
        f"Expected 2 L01-L02 collisions (one per frame), got {len(l01_l02)}"
    )
    max_vel = max(e["response_velocity"] for e in l01_l02)
    assert abs(max_vel - 3.603748) < 0.0001, (
        f"Expected L01-L02 max velocity=3.603748, got {max_vel}"
    )


def test_summary_fields_complete():
    """Summary must contain all required fields with correct types."""
    summary = load_summary()
    assert "total_collisions" in summary
    assert "unique_pairs" in summary
    assert "avg_response_velocity" in summary
    assert "max_response_velocity" in summary
    assert "cells_with_collisions" in summary
    assert isinstance(summary["total_collisions"], int)
    assert isinstance(summary["unique_pairs"], int)
    assert isinstance(summary["avg_response_velocity"], float)
    assert isinstance(summary["max_response_velocity"], float)
    assert isinstance(summary["cells_with_collisions"], int)
