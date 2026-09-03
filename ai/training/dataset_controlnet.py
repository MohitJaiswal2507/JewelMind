"""JewelMind ControlNet Paired Dataset Loader.

Loads paired conditioning lineart maps and target jewellery photographs along with
prompts and metadata for ControlNet training and validation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image

import torch
from torch.utils.data import Dataset
from torchvision import transforms

logger = logging.getLogger("jewelmind.dataset_controlnet")


def resolve_file_path(
    candidate_path: Union[str, Path],
    primary_dir: Path,
    fallback_dirs: Optional[List[Path]] = None,
) -> Path:
    """Resolve a relative or absolute file path against primary and fallback directories."""
    p = Path(candidate_path)
    if p.is_absolute() and p.exists():
        return p

    # Check direct relative to primary_dir
    p1 = primary_dir / p
    if p1.exists():
        return p1

    # Check relative to fallback directories
    if fallback_dirs:
        for fb_dir in fallback_dirs:
            p_fb = fb_dir / p
            if p_fb.exists():
                return p_fb
            # Check by filename inside fallback
            p_fb_name = fb_dir / p.name
            if p_fb_name.exists():
                return p_fb_name

    # Check workspace root
    p_root = Path(candidate_path)
    if p_root.exists():
        return p_root

    raise FileNotFoundError(
        f"Could not resolve file path '{candidate_path}' in primary directory '{primary_dir}' "
        f"or fallbacks {[str(d) for d in (fallback_dirs or [])]}."
    )


class ControlNetJewelleryDataset(Dataset):
    """Dataset for paired ControlNet fine-tuning on jewellery lineart and target photos.

    Loads:
      - Conditioning image (LineArt map -> [0, 1] RGB tensor)
      - Target jewellery photograph (Photorealistic image -> [-1, 1] RGB tensor)
      - Tokenized caption/prompt (CLIP input IDs)
      - Metadata attributes (category, edge density, paths)
    """

    def __init__(
        self,
        data_dir: Union[str, Path] = "datasets/controlnet_paired",
        metadata_file: Optional[Union[str, Path]] = None,
        tokenizer: Optional[Any] = None,
        size: int = 512,
        keep_aspect_ratio: bool = True,
        max_samples: Optional[int] = None,
    ):
        self.data_dir = Path(data_dir).resolve()
        self.tokenizer = tokenizer
        self.size = size
        self.keep_aspect_ratio = keep_aspect_ratio
        self.max_samples = max_samples
        self.entries: List[Dict[str, Any]] = []

        # Resolve metadata file location
        if metadata_file and Path(metadata_file).exists():
            self.meta_file = Path(metadata_file).resolve()
        elif (self.data_dir / "metadata" / "train.jsonl").exists():
            self.meta_file = self.data_dir / "metadata" / "train.jsonl"
        elif (self.data_dir / "train.jsonl").exists():
            self.meta_file = self.data_dir / "train.jsonl"
        elif (self.data_dir / "metadata.jsonl").exists():
            self.meta_file = self.data_dir / "metadata.jsonl"
        else:
            raise FileNotFoundError(f"No valid metadata JSONL file found in {self.data_dir} or {metadata_file}")

        # Parse JSONL records
        with open(self.meta_file, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    record = json.loads(line_str)
                    self.entries.append(record)
                except json.JSONDecodeError as exc:
                    logger.warning("Skipping invalid JSON on line %d in %s: %s", line_idx, self.meta_file, exc)

        if max_samples is not None and max_samples > 0:
            self.entries = self.entries[:max_samples]

        if not self.entries:
            raise ValueError(f"No records loaded from metadata file: {self.meta_file}")

        # Fallback search directories for paths
        self.fallback_dirs = [
            self.data_dir,
            self.data_dir / "images",
            self.data_dir / "conditioning",
            self.data_dir.parent / "controlnet_paired",
            Path("datasets/controlnet_paired"),
            Path("datasets/controlnet_paired/images"),
            Path("datasets/controlnet_paired/conditioning"),
        ]

        # Target image transform: scale to [-1, 1] for VAE latent encoding
        self.target_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ])

        # Conditioning image transform: scale to [0, 1] for ControlNet input
        self.cond_transform = transforms.Compose([
            transforms.ToTensor(),
        ])

    def __len__(self) -> int:
        return len(self.entries)

    def _letterbox_image(self, image: Image.Image, pad_color: Union[int, tuple]) -> Image.Image:
        """Resize image preserving aspect ratio with letterbox padding to (size, size)."""
        w, h = image.size
        if w == self.size and h == self.size:
            return image

        scale = min(self.size / w, self.size / h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))

        resized = image.resize((new_w, new_h), Image.Resampling.BILINEAR)
        fill_color = pad_color if isinstance(pad_color, tuple) else (pad_color, pad_color, pad_color)
        padded = Image.new("RGB", (self.size, self.size), fill_color)
        paste_x = (self.size - new_w) // 2
        paste_y = (self.size - new_h) // 2
        padded.paste(resized, (paste_x, paste_y))
        return padded

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        entry = self.entries[idx]

        # 1. Resolve target image path
        target_key = entry.get("target") or entry.get("image") or entry.get("target_image") or entry.get("file_name")
        if not target_key:
            raise KeyError(f"Record {idx} missing target image key ('target', 'image', or 'file_name').")

        target_path = resolve_file_path(target_key, self.data_dir, self.fallback_dirs)

        # 2. Resolve conditioning image path
        cond_key = (
            entry.get("source")
            or entry.get("conditioning")
            or entry.get("conditioning_path")
            or entry.get("conditioning_image")
        )
        if not cond_key:
            # Fallback by stem matching if source key not explicit
            stem = Path(target_key).stem
            cond_key = f"conditioning/{stem}.png"

        cond_path = resolve_file_path(cond_key, self.data_dir, self.fallback_dirs)

        # 3. Load target image
        try:
            target_img = Image.open(target_path).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Failed to load target image '{target_path}': {exc}")

        # 4. Load conditioning image
        try:
            cond_img = Image.open(cond_path).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Failed to load conditioning image '{cond_path}': {exc}")

        # 5. Apply aspect-ratio preserving letterbox or direct resize
        if self.keep_aspect_ratio:
            # Target photo letterboxed with white padding (255, 255, 255)
            target_img = self._letterbox_image(target_img, pad_color=(255, 255, 255))
            # Conditioning lineart letterboxed with black padding (0, 0, 0)
            cond_img = self._letterbox_image(cond_img, pad_color=(0, 0, 0))
        else:
            target_img = target_img.resize((self.size, self.size), Image.Resampling.BILINEAR)
            cond_img = cond_img.resize((self.size, self.size), Image.Resampling.BILINEAR)

        # 6. Tensor conversion and normalization
        pixel_values = self.target_transform(target_img)  # [-1, 1]
        conditioning_pixel_values = self.cond_transform(cond_img)  # [0, 1]

        # 7. Prompt handling & Tokenization
        prompt_text = (
            entry.get("prompt")
            or entry.get("caption")
            or entry.get("text")
            or ""
        ).strip()

        if self.tokenizer is not None:
            max_len = getattr(self.tokenizer, "model_max_length", 77)
            token_out = self.tokenizer(
                prompt_text,
                padding="max_length",
                truncation=True,
                max_length=max_len,
                return_tensors="pt",
            )
            input_ids = token_out.input_ids.squeeze(0)
        else:
            # Placeholder tensor if tokenizer not passed (e.g. unit tests)
            input_ids = torch.zeros(77, dtype=torch.long)

        sample: Dict[str, Any] = {
            "pixel_values": pixel_values,
            "conditioning_pixel_values": conditioning_pixel_values,
            "input_ids": input_ids,
            "prompt": prompt_text,
            "source_path": str(cond_path),
            "target_path": str(target_path),
        }

        # Preserve additional metadata
        for attr in ("category", "edge_density", "border_noise_density", "source_sha256", "conditioning_sha256"):
            if attr in entry:
                sample[attr] = entry[attr]

        return sample
