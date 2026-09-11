"""JewelMind Rendering V2 Paired Dataset Loader.

Loads paired conditioning Canny edge maps and photorealistic target jewellery
photographs along with tokenized prompts and metadata for ControlNet V2 training,
validation, and evaluation across the 8 canonical jewellery categories.
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import numpy as np
from PIL import Image

import torch
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

logger = logging.getLogger("jewelmind.rendering_v2_dataset")

# 8 Canonical Categories defined in JewelMind Rendering V2 Taxonomy
CANONICAL_CATEGORIES = [
    "ring",
    "earring",
    "pendant",
    "necklace",
    "bracelet",
    "bangle",
    "brooch",
    "other_jewellery",
]

CATEGORY_ALIASES = {
    "other": "other_jewellery",
    "other_jewellery": "other_jewellery",
    "bangles": "bangle",
    "bracelets": "bracelet",
    "earrings": "earring",
    "necklaces": "necklace",
    "pendants": "pendant",
    "rings": "ring",
    "brooches": "brooch",
}


def normalize_category(category_name: str) -> str:
    """Map raw or legacy category strings to the 8 canonical categories."""
    clean = str(category_name).strip().lower()
    if clean in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[clean]
    if clean in CANONICAL_CATEGORIES:
        return clean
    return "other_jewellery"


class RenderingV2Dataset(Dataset):
    """PyTorch Dataset for paired ControlNet fine-tuning on JewelMind Rendering V2.

    Loads:
      - Conditioning Canny edge map (3-channel float32 RGB tensor normalized to [0.0, 1.0])
      - Target photorealistic image (3-channel float32 RGB tensor normalized to [-1.0, 1.0] for VAE)
      - Tokenized prompt (CLIP input IDs of shape [77]) if tokenizer is provided
      - Comprehensive metadata (category, source, paths, prompt string)
    """

    def __init__(
        self,
        split_dir: Union[str, Path] = "ai/vision/datasets/rendering_v2/train",
        metadata_file: Optional[Union[str, Path]] = None,
        tokenizer: Optional[Any] = None,
        resolution: int = 512,
        max_samples: Optional[int] = None,
        category_filter: Optional[Union[str, List[str]]] = None,
        transform_conditioning: Optional[Callable] = None,
        transform_target: Optional[Callable] = None,
    ):
        """Initialize the Rendering V2 dataset loader.

        Args:
            split_dir: Directory containing the split (e.g. `ai/vision/datasets/rendering_v2/train`).
            metadata_file: Path to `metadata.jsonl`. If None, resolves to `{split_dir}/metadata.jsonl`.
            tokenizer: Optional CLIPTokenizer instance to pre-tokenize text prompts.
            resolution: Target square resolution (default: 512).
            max_samples: Optional maximum number of samples to load (useful for pilots/smoke tests).
            category_filter: Optional category name or list of categories to filter by.
            transform_conditioning: Optional additional transform for conditioning images.
            transform_target: Optional additional transform for target images.
        """
        self.split_dir = Path(split_dir).resolve()
        self.tokenizer = tokenizer
        self.resolution = resolution
        self.max_samples = max_samples
        self.transform_conditioning = transform_conditioning
        self.transform_target = transform_target

        # Resolve metadata file
        if metadata_file is not None and Path(metadata_file).exists():
            self.metadata_file = Path(metadata_file).resolve()
        elif (self.split_dir / "metadata.jsonl").exists():
            self.metadata_file = self.split_dir / "metadata.jsonl"
        elif (self.split_dir / "train" / "metadata.jsonl").exists():
            self.metadata_file = self.split_dir / "train" / "metadata.jsonl"
        elif (self.split_dir.parent / "metadata" / f"{self.split_dir.name}.jsonl").exists():
            self.metadata_file = self.split_dir.parent / "metadata" / f"{self.split_dir.name}.jsonl"
        elif (self.split_dir / f"{self.split_dir.name}.jsonl").exists():
            self.metadata_file = self.split_dir / f"{self.split_dir.name}.jsonl"
        else:
            raise FileNotFoundError(
                f"Cannot find valid metadata.jsonl in split directory '{self.split_dir}' "
                f"or explicit path '{metadata_file}'."
            )

        # Parse category filter
        self.category_filter_set: Optional[set] = None
        if category_filter:
            if isinstance(category_filter, str):
                self.category_filter_set = {normalize_category(category_filter)}
            else:
                self.category_filter_set = {normalize_category(c) for c in category_filter}

        # Parse JSONL records
        self.entries: List[Dict[str, Any]] = []
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    record = json.loads(line_str)
                    raw_cat = record.get("canonical_category") or record.get("category", "other_jewellery")
                    cat = normalize_category(raw_cat)
                    if self.category_filter_set and cat not in self.category_filter_set:
                        continue
                    record["canonical_category"] = cat
                    record["category"] = cat
                    self.entries.append(record)
                except json.JSONDecodeError as exc:
                    logger.warning("Skipping invalid JSON line %d in %s: %s", line_idx, self.metadata_file, exc)

        if self.max_samples is not None and self.max_samples > 0:
            self.entries = self.entries[: self.max_samples]

        if not self.entries:
            raise ValueError(
                f"No valid records loaded from '{self.metadata_file}' "
                f"(filter: {self.category_filter_set}, max_samples: {self.max_samples})."
            )

        logger.info(
            "RenderingV2Dataset loaded %d samples from %s (resolution=%d, tokenizer=%s)",
            len(self.entries),
            self.metadata_file,
            self.resolution,
            "present" if self.tokenizer is not None else "none",
        )

    def __len__(self) -> int:
        return len(self.entries)

    def _resolve_image_path(self, rel_path: str, subfolder_name: str) -> Path:
        """Resolve conditioning or target image path against split and dataset root directories."""
        p = Path(rel_path)
        if p.is_absolute() and p.exists():
            return p

        # Check relative to split directory (e.g. train/conditioning/xxx.png or conditioning/xxx.png)
        p_split = self.split_dir / p
        if p_split.exists():
            return p_split

        # Check relative to parent dataset root (e.g. ai/vision/datasets/rendering_v2/train/conditioning/xxx.png)
        p_parent = self.split_dir.parent / p
        if p_parent.exists():
            return p_parent

        # Check by filename inside subfolder (e.g. train/conditioning/filename.png)
        p_sub = self.split_dir / subfolder_name / p.name
        if p_sub.exists():
            return p_sub

        # Check workspace root
        if p.exists():
            return p.resolve()

        raise FileNotFoundError(
            f"Failed to locate {subfolder_name} image '{rel_path}' in split directory '{self.split_dir}'."
        )

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Load and prepare a single paired training sample.

        Returns:
            Dictionary containing:
              - `conditioning_pixel_values`: torch.Tensor (3, 512, 512) in [0.0, 1.0]
              - `pixel_values`: torch.Tensor (3, 512, 512) in [-1.0, 1.0]
              - `input_ids`: torch.Tensor (77,) tokenized prompt (if tokenizer present)
              - `prompt`: str
              - `category`: str (canonical)
              - `source`: str
              - `conditioning_path`: str
              - `target_path`: str
        """
        entry = self.entries[idx]

        # 1. Resolve paths
        raw_cond_path = entry.get("conditioning_path") or entry.get("conditioning_image", "")
        raw_target_path = entry.get("target_path") or entry.get("target_image", "")

        if not raw_cond_path or not raw_target_path:
            raise ValueError(f"Entry {idx} is missing conditioning_path or target_path: {entry}")

        cond_path = self._resolve_image_path(raw_cond_path, "conditioning")
        target_path = self._resolve_image_path(raw_target_path, "target")

        # 2. Load and validate images
        try:
            cond_img = Image.open(cond_path).convert("RGB")
        except Exception as exc:
            raise IOError(f"Corrupt or unreadable conditioning image '{cond_path}': {exc}") from exc

        try:
            target_img = Image.open(target_path).convert("RGB")
        except Exception as exc:
            raise IOError(f"Corrupt or unreadable target image '{target_path}': {exc}") from exc

        # 3. Resize if needed (preserves square geometry)
        if cond_img.size != (self.resolution, self.resolution):
            cond_img = cond_img.resize((self.resolution, self.resolution), Image.NEAREST)
        if target_img.size != (self.resolution, self.resolution):
            target_img = target_img.resize((self.resolution, self.resolution), Image.LANCZOS)

        # 4. Normalize Conditioning Image: [0, 255] -> [0.0, 1.0] float32 tensor
        cond_np = np.array(cond_img, dtype=np.float32) / 255.0
        cond_tensor = torch.from_numpy(cond_np).permute(2, 0, 1).float()  # (3, H, W)

        if self.transform_conditioning is not None:
            cond_tensor = self.transform_conditioning(cond_tensor)

        # 5. Normalize Target Image: [0, 255] -> [-1.0, 1.0] float32 tensor for VAE latent encoding
        target_np = np.array(target_img, dtype=np.float32)
        target_np = (target_np / 127.5) - 1.0
        target_tensor = torch.from_numpy(target_np).permute(2, 0, 1).float()  # (3, H, W)

        if self.transform_target is not None:
            target_tensor = self.transform_target(target_tensor)

        # 6. Extract prompt and tokenize if tokenizer provided
        prompt_str = entry.get("prompt", "")
        if not prompt_str.strip():
            cat = entry.get("category", "jewellery")
            prompt_str = f"jewelmind professional studio photograph of luxury {cat}, 8k photorealistic"

        sample: Dict[str, Any] = {
            "conditioning_pixel_values": cond_tensor,
            "pixel_values": target_tensor,
            "prompt": prompt_str,
            "category": entry.get("canonical_category") or entry.get("category", "other_jewellery"),
            "source": entry.get("source_dataset") or entry.get("source", "unknown"),
            "conditioning_path": str(cond_path),
            "target_path": str(target_path),
        }

        if self.tokenizer is not None:
            tokens = self.tokenizer(
                prompt_str,
                max_length=self.tokenizer.model_max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )
            sample["input_ids"] = tokens.input_ids[0]

        return sample


def get_rendering_v2_dataloader(
    split_dir: Union[str, Path],
    metadata_file: Optional[Union[str, Path]] = None,
    tokenizer: Optional[Any] = None,
    batch_size: int = 1,
    shuffle: bool = True,
    num_workers: int = 0,
    resolution: int = 512,
    max_samples: Optional[int] = None,
    category_filter: Optional[Union[str, List[str]]] = None,
) -> DataLoader:
    """Create a standard PyTorch DataLoader for Rendering V2 paired data."""
    dataset = RenderingV2Dataset(
        split_dir=split_dir,
        metadata_file=metadata_file,
        tokenizer=tokenizer,
        resolution=resolution,
        max_samples=max_samples,
        category_filter=category_filter,
    )
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )
