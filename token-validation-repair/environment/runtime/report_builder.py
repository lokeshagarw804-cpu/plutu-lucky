"""Report builder — assembles the final validation report with proper ordering."""

import json
import os
import configparser


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read("/app/runtime/config.ini")
    return config


def sort_results(results, config=None):
    """Sort validation results according to configuration.

    Uses sort_field and direction from [ordering] section.
    """
    if config is None:
        config = load_config()

    sort_field = config.get("ordering", "sort_field")
    direction = config.get("ordering", "direction")
    reverse = direction == "descending"

    return sorted(results, key=lambda r: r.get(sort_field, ""), reverse=reverse)


def build_report(validation_results, batch_order=None, config=None):
    """Build the final validation report.

    Args:
        validation_results: list of dicts with token validation data
        batch_order: list of batch filenames in the order they were loaded

    Returns:
        dict representing the full report
    """
    if config is None:
        config = load_config()

    sorted_results = sort_results(validation_results, config)

    total_tokens = len(sorted_results)
    valid_count = sum(1 for r in sorted_results if r.get("signature_valid") and r.get("policy_pass"))
    expired_count = sum(1 for r in sorted_results if r.get("expired"))
    invalid_sig_count = sum(1 for r in sorted_results if not r.get("signature_valid"))

    report = {
        "summary": {
            "total_tokens": total_tokens,
            "valid_tokens": valid_count,
            "expired_tokens": expired_count,
            "invalid_signatures": invalid_sig_count
        },
        "tokens": sorted_results,
        "batch_count": len(set(r.get("batch_source", "unknown") for r in sorted_results)),
        "batch_order": batch_order if batch_order else []
    }

    return report


def write_report(report, config=None):
    """Write the validation report to the output directory."""
    if config is None:
        config = load_config()

    output_dir = config.get("tokens", "output_dir")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "validation_report.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return output_path
