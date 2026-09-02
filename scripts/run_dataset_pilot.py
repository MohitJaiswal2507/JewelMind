"""Runner script for JewelMind Dataset Pilot Run.

Executes pilot collection of approximately 20 candidates from verified
open-access museum sources, applies quality filtering, deduplication,
and outputs pilot manifest and report.
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure workspace root is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.dataset_pipeline.curator import DatasetCurator

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("jewelmind.dataset.pilot_runner")


def main():
    parser = argparse.ArgumentParser(description="JewelMind Pilot Dataset Acquisition Runner")
    parser.add_argument("--limit", type=int, default=20, help="Total candidate targets to harvest for pilot (default: 20)")
    parser.add_argument("--threshold", type=int, default=6, help="Hamming distance threshold for near-duplicate rejection (default: 6)")
    parser.add_argument("--output", type=str, default="datasets/curation", help="Output directory for pilot artifacts")
    args = parser.parse_args()

    curator = DatasetCurator(
        output_dir=args.output,
        hamming_threshold=args.threshold,
    )

    entries = curator.run_pilot(target_limit=args.limit)

    accepted = [e for e in entries if e.status == "ACCEPTED"]
    logger.info("=" * 60)
    logger.info("PILOT RUN COMPLETE: %d fetched, %d accepted, %d rejected", len(entries), len(accepted), len(entries) - len(accepted))
    logger.info("Report generated at: %s/PILOT_DATASET_REPORT.md", args.output)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
