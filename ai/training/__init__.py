"""JewelMind Generative AI Training Module.

NOTE: Antigravity NEVER executes training commands automatically.
All model training is performed manually by the user on the local RTX 4060 GPU.
"""

from ai.training.dataset_controlnet import ControlNetJewelleryDataset
from ai.training.validate_controlnet_dataset import validate_controlnet_dataset
from ai.training.train_controlnet import audit_trainable_parameters, get_gpu_memory_report

__all__ = [
    "ControlNetJewelleryDataset",
    "validate_controlnet_dataset",
    "audit_trainable_parameters",
    "get_gpu_memory_report",
]
