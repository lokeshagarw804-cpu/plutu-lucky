#!/usr/bin/env python3
"""Repair script for the dependency graph resolution system."""
import os
import sys


def patch_scope_filter():
    """Fix: scope filter parsing does not strip whitespace."""
    path = "/app/runtime/scope_filter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._excluded = set(raw_excluded.split(","))',
        'self._excluded = set(s.strip() for s in raw_excluded.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_resolver_depth():
    """Fix: resolver reads max_depth from wrong config section."""
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._max_depth = config.getint("resolution", "max_depth")',
        'self._max_depth = config.getint("resolution.strict", "max_depth")'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_resolver_constraint():
    """Fix: version constraint comparator is inverted."""
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'return ver_tuple <= req_tuple\n        elif op == "<=":',
        'return ver_tuple >= req_tuple\n        elif op == "<=":'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_install_order():
    """Fix: install order sorts roots-first instead of leaves-first."""
    path = "/app/runtime/graph_builder.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda p: (p["depth"], p["package"])',
        'key=lambda p: (-p["depth"], p["scope"], p["package"])'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_checksum():
    """Fix: checksum includes install_position which is not in configured fields."""
    path = "/app/runtime/manifest_writer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        '            record["install_position"] = entry["install_position"]\n            hash_input.append(json.dumps(record, sort_keys=True))',
        '            hash_input.append(json.dumps(record, sort_keys=True))'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_scope_filter()
    patch_resolver_depth()
    patch_resolver_constraint()
    patch_install_order()
    patch_checksum()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_resolve import main as run_main
    run_main()


if __name__ == "__main__":
    main()
