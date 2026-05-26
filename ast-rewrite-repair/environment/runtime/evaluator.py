"""
AST evaluator.

Executes optimized AST statements and produces variable bindings.
"""


class Evaluator:
    """Evaluates AST statements to produce results."""

    def evaluate(self, statements):
        """Evaluate all statements and return variable bindings."""
        env = {}
        for stmt in statements:
            self._eval_stmt(stmt, env)
        return env

    def _eval_stmt(self, node, env):
        """Evaluate a single statement."""
        if node.node_type == "assign":
            value = self._eval_expr(node.attrs["value"], env)
            env[node.attrs["name"]] = value
        elif node.node_type == "if_stmt":
            cond = self._eval_expr(node.attrs["condition"], env)
            if cond:
                self._eval_stmt(node.attrs["body"], env)

    def _eval_expr(self, node, env):
        """Evaluate an expression node."""
        if node.node_type == "literal":
            return node.attrs["value"]
        elif node.node_type == "varref":
            return env.get(node.attrs["name"], 0)
        elif node.node_type == "binop":
            left = self._eval_expr(node.attrs["left"], env)
            right = self._eval_expr(node.attrs["right"], env)
            return self._apply_op(node.attrs["op"], left, right)
        elif node.node_type == "compare":
            left = self._eval_expr(node.attrs["left"], env)
            right = self._eval_expr(node.attrs["right"], env)
            return self._apply_compare(node.attrs["op"], left, right)
        return 0

    def _apply_op(self, op, left, right):
        """Apply arithmetic operator."""
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            if right == 0:
                return 0
            return left / right
        return 0

    def _apply_compare(self, op, left, right):
        """Apply comparison operator."""
        if op == ">":
            return left > right
        elif op == "<":
            return left < right
        elif op == ">=":
            return left >= right
        elif op == "<=":
            return left <= right
        elif op == "==":
            return left == right
        return False
