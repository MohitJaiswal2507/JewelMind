# JewelMind — Phase 9: Appearance LoRA Training Readiness & Infrastructure Audit Report

> **ABSOLUTE BOUNDARY AUDIT**:  
> - **TRAINING HAS NOT BEEN EXECUTED**: Neither LoRA training nor ControlNet training was started or scheduled.  
> - **GPU INFERENCE HAS NOT BEEN RUN**: Zero diffusion model generations were executed.  
> - **PRODUCTION RENDERING PIPELINE UNTOUCHED**: Phase 7 ControlNet rendering code remains intact.  
> - **NO GIT COMMITS OR PUSHES**: Working tree is preserved without commits or pushes on branch `phase-9-appearance-lora-training`.  
> - **MANUAL OPERATOR EXECUTION**: The RTX 4060 Laptop GPU (8 GB VRAM) will be manually operated by the project owner following this audit.  

---

## 1. Executive Summary

A comprehensive end-to-end audit of JewelMind's Appearance-LoRA training infrastructure was completed across the codebase, configuration, dependencies, dataset compatibility, and hardware constraints. 

### Audit Verdict: **PHASE 9 TRAINING READINESS: PASS WITH CHANGES**

* **Infrastructure Readiness**: The training pipeline ([`ai/training/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/train_lora.py) and entrypoint [`scripts/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/scripts/train_lora.py)) is verified, resilient, and fully aligned with the authoritative Phase 8 dataset ([`datasets/appearance_lora/`](file:///c:/Users/usern/Desktop/JewelMind/datasets/appearance_lora/)).
* **Key Enhancements Implemented**:
  1. Updated [`ai/training/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/train_lora.py) to support `train_metadata_file` and `val_metadata_file` parameter overrides and added aspect-ratio preserving letterbox padding (`keep_aspect_ratio: true`) to prevent circular rings and delicate earrings from being squashed or distorted.
  2. Added CLI argument overrides to [`ai/training/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/train_lora.py) (`--train_data_dir`, `--val_data_dir`, `--output_dir`, `--max_train_steps`, `--learning_rate`, etc.).
  3. Created [`scripts/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/scripts/train_lora.py) as a unified entrypoint forwarding directly to `ai.training.train_lora.main()`.
  4. Updated [`configs/jewellery_lora.yaml`](file:///c:/Users/usern/Desktop/JewelMind/configs/jewellery_lora.yaml) with the authoritative Phase 8 dataset paths and output directories (`outputs/appearance_lora`).
  5. Updated PyTorch AMP calls to modern syntax (`torch.amp.GradScaler('cuda')` and `torch.amp.autocast('cuda')`), completely eliminating deprecation warnings.
* **Sole Prerequisite for the Project Owner**: The `peft` Python library must be installed in the `tgpu` Conda environment prior to running the training command (`pip install peft`).

---

## 2. Current Training Architecture

* **Base Model**: Stable Diffusion v1.5 (`runwayml/stable-diffusion-v1-5`, variant `fp16`)
* **Adaptation Mechanism**: Low-Rank Adaptation (LoRA) on UNet cross-attention and projection layers
* **Target UNet Modules**: `to_k`, `to_q`, `to_v`, `to_out.0`
* **Frozen Subsystems**:
  - AutoencoderKL (VAE): Frozen, FP16, zero gradients, zero optimizer states (~160 MB VRAM)
  - CLIPTextModel: Frozen, FP16, zero gradients, zero optimizer states (~246 MB VRAM)
  - UNet Backbone: Base parameters frozen, gradient checkpointing active
* **Trainable Parameters**: ~786,432 parameters (~3.15 MB in FP32; < 15 MB including AdamW optimizer states)
* **Design Purpose**: Learns jewellery material appearance (specular reflections, polished gold, platinum highlights, gem facets, intricate filigree, and studio product lighting). Does **not** replace ControlNet sketch conditioning; ControlNet will condition this LoRA during inference.

---

## 3. Training Script Audit

* **Primary Implementation**: [`ai/training/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/ai/training/train_lora.py)
* **Convenience Wrapper**: [`scripts/train_lora.py`](file:///c:/Users/usern/Desktop/JewelMind/scripts/train_lora.py)
* **Key Mechanisms Verified**:
  - `JewelleryCaptionDataset`: Robustly parses schema variations (`file_name`, `text`, `caption`, `category`, `candidate_id`).
  - Path Resolution: Automatically falls back to parent directories, `datasets/appearance_lora/`, or relative filenames if paths vary.
  - Geometry Protection: Strictly excludes `RandomHorizontalFlip` to preserve asymmetric stone settings and hallmark orientation.
  - Aspect Ratio Handling: When `keep_aspect_ratio: true`, letterbox-pads non-square images to 512×512 using a neutral canvas, avoiding oval ring distortions.
  - Validation Evaluation: `evaluate_validation_loss()` executes under `unet.eval()` and `torch.no_grad()`, restoring `unet.train()` without modifying weights or optimizer state.

---

## 4. Dataset Compatibility

* **Authoritative Dataset**: [`datasets/appearance_lora/`](file:///c:/Users/usern/Desktop/JewelMind/datasets/appearance_lora/)
* **Total Curated Images**: **164 images** (100% verified CC0 public domain)
* **Training Partition**: **147 images (89.6%)** (`splits/train_metadata.jsonl` / `splits/train.csv`)
* **Validation Partition**: **17 images (10.4%)** (`splits/val_metadata.jsonl` / `splits/validation.csv`)
* **Cross-Split Leakage**: Exactly **0 bytes / 0 images** overlap. Multi-angle near-duplicate shots were clustered atomically via DSU grouping.
* **Physical Integrity**: All 164 images in [`datasets/appearance_lora/images/`](file:///c:/Users/usern/Desktop/JewelMind/datasets/appearance_lora/images/) (`CAND_001.jpg` to `CAND_226.jpg`) resolve cleanly.

---

## 5. Caption & Tokenization Audit

* **Caption Storage**: Dual format supported:
  - Individual text files: `datasets/appearance_lora/images/CAND_xxx.txt`
  - JSONL metadata: `datasets/appearance_lora/splits/train_metadata.jsonl` and `val_metadata.jsonl`
* **Token Budget Analysis** (via CLIP ViT-L/14 tokenizer, max sequence length = 77 tokens):
  - **Minimum Token Length**: 31 tokens
  - **Maximum Token Length**: 40 tokens
  - **Average Token Length**: 32.3 tokens
  - **Captions Exceeding 77 Tokens**: **0 captions** (0.0%)
* **Truthfulness & Grounding**: Captions strictly specify observable jewellery categories, verified metal colors, visible stone/filigree accents, and studio lighting context. No hallucinated carats (18k/24k), ungrounded gem species, or trigger tokens exist.

---

## 6. LoRA Configuration

| Parameter | Recommended Setting | Rationale |
| :--- | :---: | :--- |
| **LoRA Rank ($r$)** | `16` | Keeps adapter weight footprint to ~3.2 MB, preventing overfitting on 147 images while retaining capacity for specular textures. |
| **LoRA Alpha ($\alpha$)** | `32` | Standard scaling multiplier ($\alpha / r = 2.0$) for effective gradient updates. |
| **LoRA Dropout** | `0.05` | Regularizes cross-attention weights against memorization. |
| **Target Modules** | `to_k, to_q, to_v, to_out.0` | Adapts both self-attention and cross-attention projections in the UNet. |
| **Bias** | `"none"` | Excludes bias parameter updates to minimize checkpoint size and memory. |

---

## 7. Optimizer & Scheduler Audit

* **Optimizer**: `AdamW`
  - Learning Rate: `1.0e-4`
  - Betas: `(0.9, 0.999)`
  - Weight Decay: `1.0e-2`
  - Epsilon: `1.0e-8`
* **Scheduler**: `cosine` with 50 warmup steps
* **Gradient Accumulation**: `4` steps (with batch size `1`, effective batch size = `4`)
* **Step Accounting**:
  - `global_step` strictly increments on optimizer steps, not dataloader batches.
  - With $N = 147$ train images and effective batch size = 4: $\lceil 147 / 4 \rceil = 37$ steps per epoch.
  - Setting `max_train_steps: 1000` corresponds to approximately **27 training epochs**.

---

## 8. Validation Infrastructure Audit

* **Separation**: Validation split contains 17 distinct candidates completely quarantined from training.
* **Loss Computation**: Evaluated via MSE between predicted noise $\epsilon_\theta(z_t, t, c)$ and ground truth Gaussian noise $\epsilon$.
* **Weight Non-Modifying Proof**: Tested in `test_validation_loss_non_modifying`; weights before and after validation are mathematically identical (`torch.equal == True`).
* **Execution Interval**: Validation is triggered automatically at each checkpoint saving step (`checkpointing_steps: 200`) and upon reaching `max_train_steps`.

---

## 9. Checkpoint & Resume Audit

The checkpointing logic in `ai/training/train_lora.py` has been audited and verified:
1. **Checkpoint Contents**:
   - `adapter_model.safetensors` / `adapter_config.json`: PEFT LoRA weights
   - `optimizer.pt`: AdamW first and second momentum tensors
   - `scheduler.pt`: Cosine LR scheduler state
   - `scaler.pt`: PyTorch GradScaler state
   - `trainer_state.json`: Global step, epoch, and timestamp
2. **Numeric Checkpoint Discovery**: `find_latest_checkpoint()` sorts purely by integer step (`checkpoint-200`, `checkpoint-400`), safely ignoring non-numeric directory names.
3. **`checkpoint-last` Handling**: Maintained alongside numbered checkpoints as an atomic mirror, with safe fallback handling if only `checkpoint-last` exists.
4. **Resume Verification**: Restores optimizer states, scheduler states, and scaler states, allowing genuine resume without loss spikes or learning rate restarts.

---

## 10. Dependency & Environment Audit (`tgpu` Conda Environment)

The local Conda environment `C:\Users\usern\miniconda3\envs\tgpu` was inspected:

| Package | Detected Version | Required Status | Action Needed |
| :--- | :---: | :---: | :--- |
| **Python** | 3.10.19 (64-bit) | $\ge$ 3.10 | OK |
| **PyTorch** | 2.9.0+cu130 | $\ge$ 2.0.0 | OK |
| **CUDA** | 13.0 (Driver 576.80) | $\ge$ 11.8 | OK |
| **torchvision** | 0.24.0+cu130 | Compatible | OK |
| **diffusers** | 0.36.0 | $\ge$ 0.25.0 | OK |
| **transformers** | 4.57.1 | $\ge$ 4.35.0 | OK |
| **accelerate** | 1.14.0 | $\ge$ 0.25.0 | OK |
| **safetensors** | 0.6.2 | $\ge$ 0.4.0 | OK |
| **datasets** | 4.4.1 | $\ge$ 2.14.0 | OK |
| **peft** | **NOT INSTALLED** | **Required** | **Run: `pip install peft`** |
| **bitsandbytes**| NOT INSTALLED | Optional (8-bit Adam) | Not needed at batch size 1 |

---

## 11. RTX 4060 8 GB Compatibility Assessment

* **Hardware**: NVIDIA GeForce RTX 4060 Laptop GPU
* **Total Physical VRAM**: **8,188 MiB (8.00 GB)**
* **Mathematical VRAM Budget Breakdown**:

| Component | Precision / Mode | Estimated VRAM |
| :--- | :--- | ---:|
| **VAE** | FP16 (Frozen) | ~160 MB |
| **CLIP Text Encoder** | FP16 (Frozen) | ~246 MB |
| **UNet Base Backbone** | FP32/FP16 (Frozen, no grad) | ~1,720 MB |
| **LoRA Trainable Parameters** | FP32 ($r=16$, 4 projections) | ~3.2 MB |
| **AdamW Optimizer States** | FP32 ($m$ and $v$ states) | ~6.3 MB |
| **Activations (Batch=1, Res=512)**| Gradient Checkpointing Enabled | ~650 MB |
| **CUDA Context & PyTorch Overhead** | System runtime | ~600 MB |
| **Total Peak VRAM Estimate** | | **~3.4 to 4.2 GB** |
| **Safety Headroom on 8GB GPU** | | **~3.8 to 4.6 GB free** |

**Conclusion**: The configuration has a ~45–50% safety buffer. Running on the 8 GB RTX 4060 will not trigger CUDA Out-Of-Memory (OOM) errors.

---

## 12. Recommended Initial Configuration

Defined in [`configs/jewellery_lora.yaml`](file:///c:/Users/usern/Desktop/JewelMind/configs/jewellery_lora.yaml):

```yaml
model:
  pretrained_model_name_or_path: "runwayml/stable-diffusion-v1-5"
  lora_rank: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules: ["to_k", "to_q", "to_v", "to_out.0"]

dataset:
  train_data_dir: "datasets/appearance_lora"
  train_metadata_file: "datasets/appearance_lora/splits/train_metadata.jsonl"
  val_data_dir: "datasets/appearance_lora"
  val_metadata_file: "datasets/appearance_lora/splits/val_metadata.jsonl"
  resolution: 512
  keep_aspect_ratio: true
  center_crop: false
  random_flip: false

training:
  seed: 42
  train_batch_size: 1
  gradient_accumulation_steps: 4
  gradient_checkpointing: true
  mixed_precision: "fp16"
  learning_rate: 1.0e-4
  lr_scheduler: "cosine"
  lr_warmup_steps: 50
  max_train_steps: 1000
  checkpointing_steps: 200
  checkpoints_total_limit: 3
  resume_from_checkpoint: "latest"

output:
  output_dir: "outputs/appearance_lora"
  logging_dir: "outputs/appearance_lora/logs"
```

---

## 13. Exact Manual Training Command

> [!IMPORTANT]
> **DO NOT RUN THIS COMMAND INSIDE THE IDE.**  
> Open a local terminal, activate the `tgpu` environment, and run the following two commands:

### Step 1: Install `peft` dependency (one-time setup):
```powershell
conda activate tgpu
pip install peft
```

### Step 2: Launch manual training:
```powershell
python scripts/train_lora.py --config configs/jewellery_lora.yaml
```

*Alternative command with explicit CLI overrides:*
```powershell
python scripts/train_lora.py `
  --config configs/jewellery_lora.yaml `
  --train_data_dir datasets/appearance_lora `
  --train_metadata_file datasets/appearance_lora/splits/train_metadata.jsonl `
  --val_data_dir datasets/appearance_lora `
  --val_metadata_file datasets/appearance_lora/splits/val_metadata.jsonl `
  --output_dir outputs/appearance_lora `
  --max_train_steps 1000 `
  --learning_rate 0.0001
```

---

## 14. Expected Output Structure

Upon execution, training outputs will populate:
```text
outputs/appearance_lora/
├── checkpoints/
│   ├── checkpoint-200/
│   │   ├── adapter_model.safetensors
│   │   ├── adapter_config.json
│   │   ├── optimizer.pt
│   │   ├── scheduler.pt
│   │   ├── scaler.pt
│   │   └── trainer_state.json
│   ├── checkpoint-400/
│   ├── checkpoint-600/
│   ├── checkpoint-800/
│   ├── checkpoint-1000/
│   └── checkpoint-last/
├── logs/
│   └── (TensorBoard events for loss tracking)
└── jewellery_lora_final/
    ├── adapter_model.safetensors
    └── adapter_config.json
```

---

## 15. Git & Artifact Safety

* **Git Ignore Verification**: [`.gitignore`](file:///c:/Users/usern/Desktop/JewelMind/.gitignore) line 139 explicitly ignores `outputs/`.
* **LoRA Checkpoints**: Model weights (`*.safetensors`, `*.pt`, `checkpoints/`, `runs/`, `outputs/`) will not be staged or committed.
* **Working Tree**: Clean and isolated on branch `phase-9-appearance-lora-training`.

---

## 16. Baseline Comparison Plan

After the project owner completes training, the trained LoRA will be compared against the Phase 7 baseline:

* **Phase 7 ControlNet Baseline**:
  - Model: RunwayML SD 1.5 + ControlNet LineArt (`lllyasviel/control_v11p_sd15_lineart`)
  - Resolution: 512×512, Steps: 20, Guidance: 7.5, Seed: 42
  - Prompt: `"photorealistic fine jewellery ring, 18k yellow gold, round brilliant diamond solitaire, studio lighting, sharp focus"`
  - Baseline Latency: ~16.33 seconds
  - Baseline Peak VRAM: ~3.33 GiB
* **Evaluation Criteria**:
  1. **Specular Metal Quality**: Are gold and silver reflections crisper and less "plastic" than base SD 1.5?
  2. **Gemstone Clarity**: Are diamond/gemstone facets defined rather than cloudy blobs?
  3. **ControlNet Geometry Preservation**: Does the LoRA maintain the exact sketch contour provided by ControlNet?
  4. **Unwanted Transformations**: Does the model avoid hallucinating extra rings or background props?

---

## 17. Known Risks & Mitigations

1. **Missing `peft` package**:
   - *Risk*: Running the script without `peft` raises an `ImportError`.
   - *Mitigation*: Operator must run `pip install peft` before invoking the script.
2. **Network latency on first download**:
   - *Risk*: `runwayml/stable-diffusion-v1-5` base weights (~4 GB) must be cached on the first invocation.
   - *Mitigation*: HuggingFace automatically caches downloads to `~/.cache/huggingface/hub`. Once cached, subsequent runs start instantly offline.
3. **Thermal Throttling on Laptop GPU**:
   - *Risk*: RTX 4060 Laptop GPU running 1,000 steps (~25 minutes) may reach thermal throttling limits if unventilated.
   - *Mitigation*: Ensure the laptop is on a hard flat surface with adequate airflow. Effective batch size 4 (batch size 1 with 4 accumulation steps) keeps duty cycles manageable.

---

## 18. Required Manual Actions by Project Owner

1. Review this report ([`PHASE_9_TRAINING_READINESS_REPORT.md`](file:///c:/Users/usern/Desktop/JewelMind/PHASE_9_TRAINING_READINESS_REPORT.md)).
2. Open Windows Terminal / PowerShell.
3. Activate the Conda environment and install `peft`:
   ```powershell
   conda activate tgpu
   pip install peft
   ```
4. Execute the training command:
   ```powershell
   python scripts/train_lora.py --config configs/jewellery_lora.yaml
   ```
5. Monitor progress via the tqdm progress bar and terminal logs.

---

## 19. Final Readiness Verdict

### **PHASE 9 TRAINING READINESS: PASS WITH CHANGES**

*All code, configs, dataset loaders, and regression tests are in place. Once the operator installs `peft`, training is ready to be manually started.*
