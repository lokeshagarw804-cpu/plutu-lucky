"""
Scope-based package filter.

Filters packages based on the configured excluded scope list.
Packages with excluded scopes are removed before dependency
resolution to reduce the graph to production-relevant nodes.
"""

import configparser


class ScopeFilter:
    """Filters packages by scope exclusion rules."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        raw_excluded = config.get("scopes", "excluded_scopes")
        self._excluded = set(raw_excluded.split(","))
        self._include_trans = config.getboolean(
            "scopes", "include_transitives"
        )

    def filter_packages(self, packages):
        """Remove packages whose scope is in the excluded set."""
        return [
            p for p in packages
            if p["scope"] not in self._excluded
        ]
