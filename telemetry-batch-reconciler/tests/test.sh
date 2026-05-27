#!/usr/bin/env bash

# Run the reconciler to produce output
pushd /environment > /dev/null
python3 -c "
import sys
sys.path.insert(0, '.')
from runtime.run_reconciler import main
main()
" 2>&1
popd > /dev/null

# Run tests against the output
pytest tests/test_outputs.py -rA
