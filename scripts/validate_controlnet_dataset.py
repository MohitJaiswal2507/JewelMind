"""JewelMind ControlNet Dataset Validator CLI Entrypoint.

Delegates execution to ai.training.validate_controlnet_dataset.main().
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.training.validate_controlnet_dataset import main

if __name__ == "__main__":
    main()
