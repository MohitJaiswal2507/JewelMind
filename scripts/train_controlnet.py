"""JewelMind ControlNet Training Command-Line Entrypoint.

Delegates execution to ai.training.train_controlnet.main() while preserving CLI arguments.

Usage:
    # 1-step manual GPU smoke test:
    python scripts/train_controlnet.py --config configs/controlnet_jewellery.yaml --smoke_test

    # Resuming manual training:
    python scripts/train_controlnet.py --config configs/controlnet_jewellery.yaml --resume latest
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.training.train_controlnet import main

if __name__ == "__main__":
    main()
