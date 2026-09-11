"""Tests for PEFT LoRA loading into UNet2DConditionModel."""

import json
from pathlib import Path
import pytest
import torch
from diffusers import UNet2DConditionModel
from safetensors.torch import save_file

from ai.training.inference import load_peft_lora_to_unet


@pytest.fixture
def dummy_peft_lora_dir(tmp_path: Path) -> Path:
    """Creates a synthetic PEFT LoRA adapter checkpoint with PEFT-style keys."""
    lora_dir = tmp_path / "mock_peft_lora"
    lora_dir.mkdir(parents=True, exist_ok=True)

    # adapter_config.json
    adapter_config = {
        "base_model_name_or_path": None,
        "bias": "none",
        "fan_in_fan_out": False,
        "inference_mode": True,
        "init_lora_weights": True,
        "layers_pattern": None,
        "layers_to_transform": None,
        "loftq_config": {},
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "modules_to_save": None,
        "peft_type": "LORA",
        "r": 16,
        "rank_pattern": {},
        "revision": None,
        "target_modules": ["to_k", "to_q", "to_v", "to_out.0"],
        "task_type": None,
        "use_dora": False,
        "use_rslora": False,
    }
    with open(lora_dir / "adapter_config.json", "w") as f:
        json.dump(adapter_config, f, indent=2)

    # adapter_model.safetensors with PEFT-style prefix 'base_model.model.'
    state_dict = {}
    # down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q
    # rank 16, in_features 320, out_features 320
    state_dict["base_model.model.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_A.weight"] = (
        torch.randn(16, 320, dtype=torch.float32)
    )
    state_dict["base_model.model.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_B.weight"] = (
        torch.randn(320, 16, dtype=torch.float32)
    )
    # down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_k
    state_dict["base_model.model.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_k.lora_A.weight"] = (
        torch.randn(16, 320, dtype=torch.float32)
    )
    state_dict["base_model.model.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_k.lora_B.weight"] = (
        torch.randn(320, 16, dtype=torch.float32)
    )

    save_file(state_dict, str(lora_dir / "adapter_model.safetensors"))
    return lora_dir


def test_load_peft_lora_to_unet_success(dummy_peft_lora_dir: Path):
    """Verifies that load_peft_lora_to_unet correctly injects PEFT adapter weights into UNet and preserves configuration."""
    unet = UNet2DConditionModel(
        sample_size=64,
        in_channels=4,
        out_channels=4,
        layers_per_block=1,
        block_out_channels=(320,),
        down_block_types=("CrossAttnDownBlock2D",),
        up_block_types=("CrossAttnUpBlock2D",),
        cross_attention_dim=768,
        attention_head_dim=8,
    )

    # Initially, UNet has 0 LoRA modules
    initial_lora_modules = [m for m in unet.modules() if hasattr(m, "lora_A")]
    assert len(initial_lora_modules) == 0

    # Load LoRA adapter
    load_peft_lora_to_unet(unet, str(dummy_peft_lora_dir), adapter_name="jewellery_lora")

    # Verify adapter registration and exact preserved config
    assert hasattr(unet, "peft_config")
    assert "jewellery_lora" in unet.peft_config
    cfg = unet.peft_config["jewellery_lora"]
    assert cfg.r == 16
    assert cfg.lora_alpha == 32
    assert cfg.lora_dropout == 0.05

    active_adapters = unet.active_adapters() if callable(unet.active_adapters) else unet.active_adapters
    assert "jewellery_lora" in active_adapters

    # Verify LoRA modules were actually injected
    injected_modules = [name for name, mod in unet.named_modules() if hasattr(mod, "lora_A")]
    assert len(injected_modules) >= 2
    assert any("attn1.to_q" in name for name in injected_modules)
    assert any("attn1.to_k" in name for name in injected_modules)


def test_load_peft_lora_missing_directory_raises():
    """Verifies that a non-existent path raises FileNotFoundError."""
    unet = UNet2DConditionModel(
        sample_size=64,
        in_channels=4,
        out_channels=4,
        layers_per_block=1,
        block_out_channels=(320,),
        down_block_types=("CrossAttnDownBlock2D",),
        up_block_types=("CrossAttnUpBlock2D",),
        cross_attention_dim=768,
        attention_head_dim=8,
    )

    with pytest.raises(FileNotFoundError):
        load_peft_lora_to_unet(unet, "non_existent/path/to/lora")


def test_real_checkpoint_400_configuration_preserved():
    """Verifies that loading real LoRA checkpoint preserves exact r=16, lora_alpha=32, lora_dropout=0.05."""
    checkpoint_dir = Path("outputs/appearance_lora/jewellery_lora_final")
    if not checkpoint_dir.exists():
        checkpoint_dir = Path("outputs/appearance_lora/checkpoints/checkpoint-400")
    if not checkpoint_dir.exists():
        pytest.skip("No appearance LoRA model present in outputs directory.")

    unet = UNet2DConditionModel.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        subfolder="unet",
        torch_dtype=torch.float16,
    )

    load_peft_lora_to_unet(unet, str(checkpoint_dir), adapter_name="default")

    assert hasattr(unet, "peft_config")
    assert "default" in unet.peft_config
    cfg = unet.peft_config["default"]
    assert cfg.r == 16
    assert cfg.lora_alpha == 32
    assert cfg.lora_dropout == 0.05

    lora_modules = [name for name, mod in unet.named_modules() if hasattr(mod, "lora_A")]
    assert len(lora_modules) == 128  # 128 attention projection layers
