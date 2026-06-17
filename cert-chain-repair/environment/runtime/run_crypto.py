"""
Main entry point for the certificate chain verification system.

Orchestrates the full verification process:
1. Load certificates from authority data files
2. Validate each certificate against the trust store
3. Build trust chains and compute scores
4. Generate output reports
"""

from runtime.loader import load_certificates
from runtime.validator import TrustValidator
from runtime.chain_builder import ChainBuilder
from runtime.reporter import Reporter


def main():
    """Run the certificate chain verification process."""
    # Stage 1: Load certificate data
    certificates = load_certificates()

    # Stage 2: Validate against trust store
    validator = TrustValidator()
    validation_results = []
    for cert in certificates:
        result = validator.validate_certificate(cert)
        validation_results.append(result)

    # Stage 3: Build trust chains
    builder = ChainBuilder()
    chains = builder.build_chains(certificates, validation_results)

    # Stage 4: Generate reports
    reporter = Reporter()
    report, summary = reporter.generate_reports(
        certificates, validation_results, chains
    )

    print(f"Processed {report['total_certificates']} certificates")
    print(f"Valid: {report['valid_count']}, Invalid: {report['invalid_count']}")
    print(f"Chains built: {summary['total_chains']}")
    print(f"Average chain length: {summary['avg_chain_length']}")


if __name__ == "__main__":
    main()
