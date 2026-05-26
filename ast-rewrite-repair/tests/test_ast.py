"""Tests for the AST rewriting compiler."""
import json
import os
import pytest

EVAL_PATH = "/app/runtime/output/evaluation_results.json"
AST_PATH = "/app/runtime/output/optimized_ast.json"
SUMMARY_PATH = "/app/runtime/output/compiler_summary.json"

def load_eval():
    with open(EVAL_PATH) as f: return json.load(f)
def load_ast():
    with open(AST_PATH) as f: return json.load(f)
def load_summary():
    with open(SUMMARY_PATH) as f: return json.load(f)

class TestOutputStructure:
    def test_eval_exists(self):
        """Evaluation results must exist."""
        assert os.path.isfile(EVAL_PATH)
    def test_ast_exists(self):
        """Optimized AST output must exist."""
        assert os.path.isfile(AST_PATH)
    def test_summary_exists(self):
        """Compiler summary must exist."""
        assert os.path.isfile(SUMMARY_PATH)
    def test_all_programs_evaluated(self):
        """All 6 programs must produce evaluation results."""
        e = load_eval()
        assert e["total_evaluated"] == 6

class TestPrecedence:
    def test_multiply_before_add(self):
        """P01: '2 + 3 * 4' must evaluate to 14, not 20."""
        e = load_eval()
        p01 = next(p for p in e["entries"] if p["program_id"] == "P01")
        assert p01["variables"]["x"] == 14, (
            f"x = 2 + 3 * 4 should be 14, got {p01['variables']['x']}"
        )
    def test_precedence_chain(self):
        """P05: '1 + 2*3 + 4*5' must be 27."""
        e = load_eval()
        p05 = next(p for p in e["entries"] if p["program_id"] == "P05")
        assert p05["variables"]["r"] == 27, (
            f"r = 1+2*3+4*5 should be 27, got {p05['variables']['r']}"
        )

class TestConstantFolding:
    def test_division_is_float(self):
        """P02: '7 / 2' must fold to 3.5, not integer 3."""
        e = load_eval()
        p02 = next(p for p in e["entries"] if p["program_id"] == "P02")
        assert abs(p02["variables"]["a"] - 3.5) < 0.001, (
            f"a = 7/2 should be 3.5, got {p02['variables']['a']}"
        )
    def test_division_chain(self):
        """P02: c = a + b where a=3.5, b=10/3."""
        e = load_eval()
        p02 = next(p for p in e["entries"] if p["program_id"] == "P02")
        expected_c = 3.5 + 10/3
        assert abs(p02["variables"]["c"] - expected_c) < 0.01, (
            f"c should be ~{expected_c:.4f}, got {p02['variables']['c']}"
        )

class TestDeadCodeElimination:
    def test_unused_removed(self):
        """P06: 'unused' variable should be eliminated."""
        e = load_eval()
        p06 = next(p for p in e["entries"] if p["program_id"] == "P06")
        assert "unused" not in p06["variables"], (
            "Variable 'unused' should be eliminated by DCE"
        )
    def test_nested_scope_preserved(self):
        """P03: variable used inside 'if' block must NOT be eliminated.

        'total' is assigned then read inside 'if total > 50'. The DCE
        must recognize that 'total' is used in a nested conditional.
        """
        e = load_eval()
        p03 = next(p for p in e["entries"] if p["program_id"] == "P03")
        assert "total" in p03["variables"], (
            "Variable 'total' was eliminated but is used in conditional"
        )
        assert p03["variables"]["total"] == 115, (
            f"total should be 115, got {p03['variables'].get('total')}"
        )
    def test_conditional_executes(self):
        """P03: the 'if' body must execute since total > 50."""
        e = load_eval()
        p03 = next(p for p in e["entries"] if p["program_id"] == "P03")
        assert "discount" in p03["variables"], (
            "discount not computed — if block may not have executed"
        )
        assert abs(p03["variables"]["discount"] - 11.5) < 0.01

class TestAccuracy:
    def test_full_accuracy(self):
        """All 6 programs must evaluate correctly (accuracy = 1.0)."""
        s = load_summary()
        assert s["accuracy"] == 1.0, (
            f"Accuracy {s['accuracy']} < 1.0 — some programs "
            f"produced wrong results"
        )
    def test_correct_count(self):
        """All 6 programs should be marked correct."""
        s = load_summary()
        assert s["correct_evaluations"] == 6
