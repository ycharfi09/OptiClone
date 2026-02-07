#!/usr/bin/env python
"""
main.py — OptiClone application entry point.
"""

import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / ".opticlone.log"),
    ],
)

logger = logging.getLogger("opticlone")


def main() -> int:
    """Main entry point."""
    logger.info("OptiClone starting…")
    try:
        from opticlone.ui_main import run_app
        run_app()
        logger.info("OptiClone closed normally.")
        return 0
    except Exception as exc:
        logger.exception("Fatal error")
        print(f"\nFATAL ERROR:\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
