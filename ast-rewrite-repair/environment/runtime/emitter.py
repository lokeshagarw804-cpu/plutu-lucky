"""
AST cost annotator and output emitter.

Computes the execution cost of optimized ASTs and generates
structured output files with optimization results.
"""

import json
import os
import configparser


class Emitter:
    """Generates output from optimized AST with cost annotations."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._ast_path = config.get("output", "ast_path")
        self._eval_path = config.get("output", "eval_path")
        self._summary_path = config.get("output", "summary_path")
        self._node_weight = config.getint("cost_model", "node_weight")
        self._op_weight = config.getint("cost_model", "operation_weight")

    def emit(self, programs, optimized_stmts, eval_results):
        """Write all output files."""
        ast_output = self._build_ast_output(programs, optimized_stmts)
        eval_output = self._build_eval_output(programs, eval_results)
        summary = self._build_summary(
            programs, optimized_stmts, eval_results
        )

        output_dir = os.path.dirname(self._ast_path)
        os.makedirs(output_dir, exist_ok=True)

        with open(self._ast_path, "w") as f:
            json.dump(ast_output, f, indent=2)
        with open(self._eval_path, "w") as f:
            json.dump(eval_output, f, indent=2)
        with open(self._summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        return ast_output, eval_output, summary

    def _build_ast_output(self, programs, optimized_stmts):
        """Build the optimized AST output."""
        entries = []
        for prog, stmts in zip(programs, optimized_stmts):
            cost = self._compute_cost(stmts)
            entries.append({
                "program_id": prog["id"],
                "name": prog["name"],
                "statement_count": len(stmts),
                "cost": cost,
                "ast": [s.to_dict() for s in stmts],
            })
        return {"total_programs": len(entries), "entries": entries}

    def _build_eval_output(self, programs, eval_results):
        """Build evaluation results output."""
        entries = []
        for prog, result in zip(programs, eval_results):
            entries.append({
                "program_id": prog["id"],
                "name": prog["name"],
                "variables": result,
            })
        return {"total_evaluated": len(entries), "entries": entries}

    def _build_summary(self, programs, optimized_stmts, eval_results):
        """Build compiler summary."""
        total_stmts = sum(len(s) for s in optimized_stmts)
        total_cost = sum(
            self._compute_cost(s) for s in optimized_stmts
        )
        correct_count = 0
        for prog, result in zip(programs, eval_results):
            expected = prog.get("expected_result", {})
            if self._results_match(expected, result):
                correct_count += 1

        return {
            "total_programs": len(programs),
            "total_statements": total_stmts,
            "total_cost": total_cost,
            "correct_evaluations": correct_count,
            "accuracy": round(correct_count / max(len(programs), 1), 4),
        }

    def _compute_cost(self, statements):
        """Compute execution cost of statement list."""
        visited = set()
        total = 0
        for stmt in statements:
            total += self._node_cost(stmt, visited)
        return total

    def _node_cost(self, node, visited):
        """Compute cost of a single node and its children.

        Uses visited set to avoid counting shared nodes multiple
        times (from CSE optimization).
        """
        if node.node_id in visited:
            return self._node_weight
        visited.add(node.node_id)

        cost = self._node_weight
        if node.node_type == "binop":
            cost += self._op_weight
            cost += self._node_cost(node.attrs["left"], visited)
            cost += self._node_cost(node.attrs["right"], visited)
        elif node.node_type == "assign":
            cost += self._node_cost(node.attrs["value"], visited)
        elif node.node_type == "if_stmt":
            cost += self._node_cost(node.attrs["condition"], visited)
            cost += self._node_cost(node.attrs["body"], visited)
        elif node.node_type == "compare":
            cost += self._op_weight
            cost += self._node_cost(node.attrs["left"], visited)
            cost += self._node_cost(node.attrs["right"], visited)

        return cost

    def _results_match(self, expected, actual):
        """Check if evaluation results match expected values."""
        for var, exp_val in expected.items():
            if var not in actual:
                return False
            act_val = actual[var]
            if isinstance(exp_val, float):
                if abs(act_val - exp_val) > 0.01:
                    return False
            else:
                if act_val != exp_val:
                    return False
        return True
