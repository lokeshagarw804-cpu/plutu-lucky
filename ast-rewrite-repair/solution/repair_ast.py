#!/usr/bin/env python3
"""Repair script for the AST rewriting compiler."""
import sys


def patch_optimizer_division():
    """Fix Bug B: constant folding uses // instead of / for division."""
    path = "/app/runtime/optimizer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "return left // right",
        "return left / right"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_optimizer_dce():
    """Fix Bug C: DCE doesn't check variables used inside if_stmt bodies."""
    path = "/app/runtime/optimizer.py"
    with open(path, "r") as f:
        content = f.read()
    # Add if_stmt handling to _collect_reads
    old_code = '''    def _collect_reads(self, node, used_vars):
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
            self._collect_reads(node.attrs["right"], used_vars)'''
    new_code = '''    def _collect_reads(self, node, used_vars):
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
            self._collect_reads(node.attrs["body"], used_vars)'''
    content = content.replace(old_code, new_code)
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_optimizer_division()
    patch_optimizer_dce()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_compiler import main as run_main
    run_main()


if __name__ == "__main__":
    main()
