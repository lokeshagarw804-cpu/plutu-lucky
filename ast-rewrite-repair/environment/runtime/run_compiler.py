"""
Main entry point for the AST rewriting compiler.

Orchestrates the compilation process:
1. Load program definitions
2. Parse source into ASTs
3. Apply optimization passes
4. Evaluate optimized ASTs
5. Emit output files
"""

import json
import os

from runtime.parser import Parser
from runtime.optimizer import Optimizer
from runtime.evaluator import Evaluator
from runtime.emitter import Emitter


def main():
    """Run the compiler."""
    # Load programs
    data_path = "/app/runtime/data/programs.json"
    with open(data_path, "r") as f:
        programs = json.load(f)

    parser = Parser()
    optimizer = Optimizer()
    evaluator = Evaluator()
    emitter = Emitter()

    all_optimized = []
    all_results = []

    for prog in programs:
        # Parse
        statements = parser.parse_program(prog["source"])

        # Optimize
        optimized = optimizer.optimize(statements)

        # Evaluate
        result = evaluator.evaluate(optimized)

        all_optimized.append(optimized)
        all_results.append(result)

    # Emit outputs
    ast_out, eval_out, summary = emitter.emit(
        programs, all_optimized, all_results
    )

    print(f"Compiled {summary['total_programs']} programs")
    print(f"Statements: {summary['total_statements']}")
    print(f"Total cost: {summary['total_cost']}")
    print(f"Accuracy: {summary['accuracy']}")


if __name__ == "__main__":
    main()
