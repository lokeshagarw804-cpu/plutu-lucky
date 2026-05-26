"""
AST optimization passes.

Applies transformations to reduce computation cost:
- Constant folding: evaluate operations on known constants at compile time
- Dead code elimination: remove assignments to unused variables
- Common subexpression elimination: reuse previously computed values
"""

import configparser
from runtime.parser import ASTNode


class Optimizer:
    """Applies optimization passes to AST statements."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._fold_constants = config.getboolean(
            "passes", "constant_folding"
        )
        self._eliminate_dead = config.getboolean(
            "passes", "dead_code_elimination"
        )
        self._cse = config.getboolean(
            "passes", "common_subexpr_elimination"
        )
        self._max_passes = config.getint("compiler", "max_passes")

    def optimize(self, statements):
        """Apply all enabled optimization passes."""
        result = list(statements)

        for _ in range(self._max_passes):
            changed = False

            if self._fold_constants:
                result, did_change = self._constant_fold_pass(result)
                changed = changed or did_change

            if self._eliminate_dead:
                result, did_change = self._dead_code_pass(result)
                changed = changed or did_change

            if self._cse:
                result, did_change = self._cse_pass(result)
                changed = changed or did_change

            if not changed:
                break

        return result

    def _constant_fold_pass(self, statements):
        """Fold operations on constant operands."""
        changed = False
        new_stmts = []
        for stmt in statements:
            new_stmt, did_fold = self._fold_node(stmt)
            new_stmts.append(new_stmt)
            if did_fold:
                changed = True
        return new_stmts, changed

    def _fold_node(self, node):
        """Recursively fold constants in a node."""
        if node.node_type == "assign":
            new_value, changed = self._fold_node(node.attrs["value"])
            if changed:
                return ASTNode("assign", name=node.attrs["name"],
                             value=new_value), True
            return node, False

        elif node.node_type == "binop":
            left, lc = self._fold_node(node.attrs["left"])
            right, rc = self._fold_node(node.attrs["right"])

            if (left.node_type == "literal" and
                    right.node_type == "literal"):
                result = self._eval_op(
                    node.attrs["op"],
                    left.attrs["value"],
                    right.attrs["value"]
                )
                if result is not None:
                    return ASTNode("literal", value=result), True

            if lc or rc:
                return ASTNode("binop", op=node.attrs["op"],
                             left=left, right=right), True
            return node, False

        elif node.node_type == "if_stmt":
            new_body, bc = self._fold_node(node.attrs["body"])
            if bc:
                return ASTNode("if_stmt",
                             condition=node.attrs["condition"],
                             body=new_body), True
            return node, False

        return node, False

    def _eval_op(self, op, left, right):
        """Evaluate a binary operation on constants."""
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            if right == 0:
                return None
            result = left / right
            if result == int(result):
                return int(result)
            return int(result)
        return None

    def _dead_code_pass(self, statements):
        """Remove assignments to variables that are never read."""
        used_vars = set()
        for stmt in statements:
            self._collect_reads(stmt, used_vars)

        # The last assignment is always live (program output)
        if statements and statements[-1].node_type == "assign":
            used_vars.add(statements[-1].attrs["name"])

        new_stmts = []
        changed = False
        for stmt in statements:
            if stmt.node_type == "assign":
                if stmt.attrs["name"] not in used_vars:
                    changed = True
                    continue
            new_stmts.append(stmt)

        return new_stmts, changed

    def _collect_reads(self, node, used_vars):
        """Collect all variable names that are read in an expression."""
        if node.node_type == "varref":
            used_vars.add(node.attrs["name"])
        elif node.node_type == "binop":
            self._collect_reads(node.attrs["left"], used_vars)
            self._collect_reads(node.attrs["right"], used_vars)
        elif node.node_type == "assign":
            self._collect_reads(node.attrs["value"], used_vars)
        elif node.node_type == "compare":
            self._collect_reads(node.attrs["left"], used_vars)
            self._collect_reads(node.attrs["right"], used_vars)
        elif node.node_type == "if_stmt":
            self._collect_reads(node.attrs["condition"], used_vars)

    def _cse_pass(self, statements):
        """Eliminate common subexpressions."""
        seen_exprs = {}
        changed = False
        new_stmts = []

        for stmt in statements:
            if stmt.node_type == "assign":
                expr_key = self._expr_signature(stmt.attrs["value"])
                if expr_key and expr_key in seen_exprs:
                    ref_name = seen_exprs[expr_key]
                    new_stmts.append(ASTNode(
                        "assign", name=stmt.attrs["name"],
                        value=ASTNode("varref", name=ref_name)
                    ))
                    changed = True
                else:
                    if expr_key:
                        seen_exprs[expr_key] = stmt.attrs["name"]
                    new_stmts.append(stmt)
            else:
                new_stmts.append(stmt)

        return new_stmts, changed

    def _expr_signature(self, node):
        """Generate a canonical string for an expression (for CSE matching)."""
        if node.node_type == "literal":
            return f"lit:{node.attrs['value']}"
        elif node.node_type == "binop":
            left_sig = self._expr_signature(node.attrs["left"])
            right_sig = self._expr_signature(node.attrs["right"])
            if left_sig and right_sig:
                return f"({left_sig}{node.attrs['op']}{right_sig})"
        return None
