#!/usr/bin/env bash
set -e

# Run the waveform correlator pipeline
python3 -m runtime.run_correlator

# Validate output with pytest
python3 -m pytest /app/tests/test_waveform_correlator.py -v
