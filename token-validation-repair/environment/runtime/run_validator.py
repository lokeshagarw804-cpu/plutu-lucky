"""Main entry point for the HMAC token batch validator."""

import json
import os
import sys

sys.path.insert(0, "/app")

from runtime.token_loader import load_batches
from runtime.signature_verifier import verify_signature, load_config as sig_config
from runtime.policy_checker import validate_token
from runtime.trust_scorer import compute_trust_score
from runtime.report_builder import build_report, write_report


def run():
    """Execute the full token validation workflow."""
    config_sig = sig_config()

    batches = load_batches()

    batch_order = [name for name, _ in batches]
    all_results = []

    for batch_name, tokens in batches:
        for token in tokens:
            sig_valid = verify_signature(token, config_sig)

            policy_result = validate_token(token)

            trust_score = compute_trust_score(token)

            result = {
                "token_id": token["token_id"],
                "batch_source": batch_name,
                "signature_valid": sig_valid,
                "expired": policy_result["expired"],
                "issuer_valid": policy_result["issuer_valid"],
                "scopes_valid": policy_result["scopes_valid"],
                "policy_pass": policy_result["policy_pass"],
                "trust_score": trust_score
            }
            all_results.append(result)

    report = build_report(all_results, batch_order=batch_order)
    output_path = write_report(report)

    print(f"Validation complete. Report written to {output_path}")
    print(f"Total tokens: {report['summary']['total_tokens']}")
    print(f"Valid tokens: {report['summary']['valid_tokens']}")
    print(f"Expired tokens: {report['summary']['expired_tokens']}")
    print(f"Invalid signatures: {report['summary']['invalid_signatures']}")

    return report


if __name__ == "__main__":
    run()
