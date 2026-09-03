"""JewelMind LoRA Training Command-Line Entrypoint.

Delegates execution to ai.training.train_lora.main() while preserving CLI arguments.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.training.train_lora import main

if __name__ == "__main__":
    main()
