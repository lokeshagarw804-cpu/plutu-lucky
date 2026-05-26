#!/usr/bin/env python3
"""Repair script for the AST rewriting compiler."""
import sys


def patch_optimizer_division():
    """Fix Bug B: constant folding truncates division results to int."""
    path = "/app/runtime/optimizer.py"
    with open(path, "r") as f:
        content = f.read()
    old_code = '''            result = left / right
            if result == int(result):
                return int(result)
            return int(result)'''
    new_code = '''            result = left / right
            if result == int(result):
                return int(result)
            return result'''
    content = content.replace(old_code, new_code)
    with open(path, "w") as f:
        f.write(content)


def patch_optimizer_dce():
    """Fix Bug C: DCE doesn't check variables used inside if_stmt bodies."""
    path = "/app/runtime/optimizer.py"
    with open(path, "r") as f:
        content = f.read()
    # Add if_stmt body traversal to _collect_reads
    old_code = '''        elif node.node_type == "if_stmt":
            self._collect_reads(node.attrs["condition"], used_vars)'''
    new_code = '''        elif node.node_type == "if_stmt":
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
