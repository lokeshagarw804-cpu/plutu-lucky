"""Particle collision detection and response simulation.

Pipeline:
  1. Load particle positions from simulation streams
  2. Group particles by simulation frame (seq number)
  3. For each frame: hash, detect candidates, resolve collisions
  4. Accumulate interaction history across frames
  5. Report statistics and write output files

Multi-frame processing allows tracking repeated interactions
between the same particle pairs across time steps.
"""
import os
import sys
from configparser import ConfigParser

from runtime.loader import ParticleLoader
from runtime.hasher import SpatialHasher
from runtime.resolver import CollisionResolver
from runtime.reporter import CollisionReporter


def run():
    config = ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(config_path)

    # Stage 1: Load particle streams
    loader = ParticleLoader(config)
    particles = loader.load_streams()

    # Group by frame (seq number)
    frames: dict[int, list[dict]] = {}
    for p in particles:
        seq = p["seq"]
        if seq not in frames:
            frames[seq] = []
        frames[seq].append(p)

    # Process each frame through the collision pipeline
    hasher = SpatialHasher(config)
    resolver = CollisionResolver(config)
    all_collisions = []

    for frame_seq in sorted(frames.keys()):
        frame_particles = frames[frame_seq]

        # Stage 2: Insert into spatial hash grid
        hasher.insert_particles(frame_particles)

        # Stage 3: Detect collision candidates
        candidate_pairs = hasher.get_candidate_pairs()

        # Stage 4: Resolve collisions
        for p1, p2, cell in candidate_pairs:
            response = resolver.resolve(p1, p2, cell)
            all_collisions.append(response)

    # Stage 5: Report statistics
    reporter = CollisionReporter(config)
    reporter.write_reports(all_collisions, resolver.get_history())


if __name__ == "__main__":
    run()
