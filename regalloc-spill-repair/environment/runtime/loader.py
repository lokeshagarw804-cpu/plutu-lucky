"""Load function IR blocks from JSON data files."""

import json
import glob
import os
import configparser


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(config_path)
    return config


def load_blocks(data_dir=None):
    """Load all IR blocks from the data directory.
    
    Each block contains:
      - block_id: identifier for the basic block
      - instructions: list of {op, dest, srcs, line} entries
      - loop_depth: nesting depth of this block (0 = top-level)
      - successors: list of successor block IDs
      - predecessors: list of predecessor block IDs
    """
    if data_dir is None:
        config = load_config()
        data_dir = config.get("input", "data_directory")
    
    pattern = os.path.join(data_dir, "block_*.json")
    files = sorted(glob.glob(pattern))
    
    blocks = []
    for fpath in files:
        with open(fpath, "r") as f:
            block = json.load(f)
        blocks.append(block)
    
    return blocks


def get_all_variables(blocks):
    """Extract all variable names from the loaded blocks."""
    variables = set()
    for block in blocks:
        for instr in block["instructions"]:
            if instr.get("dest"):
                variables.add(instr["dest"])
            for src in instr.get("srcs", []):
                variables.add(src)
    return sorted(variables)
