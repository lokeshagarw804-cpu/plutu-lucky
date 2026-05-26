"""
Repair script for the resource quota allocation ledger system.

Fixes four interacting defects:
1. quota_validator.py: reads from [limits] instead of [limits.strict]
2. integrity_checker.py: uses raw base64 key string instead of decoding it
3. ledger_loader.py: sorts files lexicographically instead of numerically
4. priority_scorer.py: uses (distance + 1) instead of distance in decay formula
"""

import importlib
import sys
import os

# --- Fix A: quota_validator.py - wrong config section ---
quota_validator_path = "/app/runtime/quota_validator.py"
with open(quota_validator_path, "r") as f:
    content = f.read()

# Change [limits] reads to [limits.strict]
content = content.replace(
    'max_units = config.getint("limits", "max_allocation_units")',
    'max_units = config.getint("limits.strict", "max_allocation_units")',
)
content = content.replace(
    'max_burst = config.getfloat("limits", "max_burst_factor")',
    'max_burst = config.getfloat("limits.strict", "max_burst_factor")',
)

with open(quota_validator_path, "w") as f:
    f.write(content)


# --- Fix B: integrity_checker.py - base64 key not decoded ---
integrity_checker_path = "/app/runtime/integrity_checker.py"
with open(integrity_checker_path, "r") as f:
    content = f.read()

# Add base64 import if not present (it's already imported, but ensure decode is used)
content = content.replace(
    'signing_key = key_str.encode("utf-8")',
    'signing_key = base64.b64decode(key_str)',
)

with open(integrity_checker_path, "w") as f:
    f.write(content)


# --- Fix C: ledger_loader.py - lexicographic sort instead of numeric ---
ledger_loader_path = "/app/runtime/ledger_loader.py"
with open(ledger_loader_path, "r") as f:
    content = f.read()

content = content.replace(
    "ledger_files = sorted(ledger_files)",
    'ledger_files = sorted(ledger_files, key=lambda f: int("".join(c for c in f if c.isdigit()) or "0"))',
)

with open(ledger_loader_path, "w") as f:
    f.write(content)


# --- Fix D: priority_scorer.py - distance + 1 in exponent ---
priority_scorer_path = "/app/runtime/priority_scorer.py"
with open(priority_scorer_path, "r") as f:
    content = f.read()

content = content.replace(
    "score = base_priority * (decay_factor ** (distance + 1))",
    "score = base_priority * (decay_factor ** distance)",
)

with open(priority_scorer_path, "w") as f:
    f.write(content)


# --- Re-run the allocator with fixes applied ---
# Clear cached modules so fixes take effect
modules_to_clear = [k for k in sys.modules if k.startswith("runtime")]
for mod in modules_to_clear:
    del sys.modules[mod]

# Re-import and run
from runtime.run_allocator import main
main()
