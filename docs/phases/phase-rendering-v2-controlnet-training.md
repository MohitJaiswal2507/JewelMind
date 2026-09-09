We are now on branch:
phase-rendering-v2-controlnet-training

Start the JewelMind Rendering V2 ControlNet Training phase.

IMPORTANT SAFETY RULES:
- Do NOT modify or overwrite any Rendering V1 model/checkpoint.
- Do NOT modify the existing production ControlNet:
  outputs/controlnet_jewellery_300/controlnet_jewellery_final
- Do NOT modify the existing Appearance LoRA.
- Do NOT modify YOLO V2.
- Do NOT integrate V2 into production yet.
- Do NOT delete existing checkpoints.
- Use the already prepared Rendering V2 dataset only.
- Do NOT download new datasets.
- Do NOT silently change the dataset.
- Training must use the RTX 4060 locally.
- Do not commit or push anything.
- First inspect the current repository and existing Rendering V1 training implementation before making changes.

REFERENCE DATASET:
ai/rendering/datasets/rendering_v2/

DATASET STATUS:
- 961 verified paired samples
- train: 664
- validation: 152
- test: 145
- 512x512 target/conditioning images
- 8 jewellery categories
- integrity checks passed
- duplicate/leakage checks passed
- final visual quality gate passed

RECOMMENDED MODEL STRATEGY:
Use the pretrained SD1.5 LineArt ControlNet as the clean V2 initialization:

lllyasviel/control_v11p_sd15_lineart

Do NOT initialize V2 from the existing 300-step JewelMind V1 checkpoint unless you explicitly document it as an experiment. The primary V2 experiment must remain a clean pretrained-LineArt-ControlNet fine-tune so we can fairly compare V1 vs V2.

TRAINING PLAN:

Stage 0 — Environment and dataset verification
- Verify RTX 4060 / CUDA.
- Verify PyTorch and Diffusers versions.
- Verify the Rendering V2 dataset exists.
- Verify train/val/test counts.
- Verify every conditioning image has its corresponding target.
- Verify image sizes and channels.
- Verify metadata/category distribution.
- Verify no V1 files will be overwritten.

Stage 1 — Training smoke test
Run a very small training smoke test before real training.

Target:
- 10 training steps maximum
- batch size 1
- gradient accumulation 4
- 512x512
- fp16
- gradient checkpointing
- SDPA/attention optimization if already supported
- frozen VAE
- frozen text encoder/CLIP
- frozen UNet
- train ControlNet only
- learning rate 1e-5

The smoke test must confirm:
- model loads
- dataset loads
- forward pass works
- backward pass works
- optimizer works
- checkpoint saving works
- no CUDA OOM
- no NaN/Inf loss

Do NOT proceed to the long training automatically if the smoke test fails.

Stage 2 — Small pilot
After the smoke test succeeds, prepare a controlled pilot of approximately 100 steps.

Save:
- checkpoint
- training loss
- validation loss if implemented
- configuration
- runtime
- peak VRAM

Do not overwrite the V1 model.

Stage 3 — Main ControlNet V2 training
Only after the pilot is healthy.

Start with:
- base: SD1.5
- ControlNet initialization: lllyasviel/control_v11p_sd15_lineart
- resolution: 512x512
- batch size: 1
- gradient accumulation: 4
- fp16
- gradient checkpointing
- learning rate: 1e-5
- optimizer: AdamW
- frozen VAE
- frozen CLIP/text encoder
- frozen UNet
- ControlNet trainable
- checkpoint every reasonable interval
- keep best and last checkpoints
- validation during training

Do NOT assume 500 steps is automatically optimal.

Treat 300/500/1000 steps as candidate stopping points.

At each useful checkpoint:
- evaluate validation loss
- inspect generated samples
- watch for overfitting
- watch for geometry degradation
- watch for hallucinated jewellery components
- watch for background contamination
- watch for loss instability
- record VRAM and runtime

If the model is already converged and additional training is not helping, stop rather than blindly continuing.

IMPORTANT:
Do not train Appearance LoRA V2 in this phase.
ControlNet V2 must be trained and evaluated independently first.

EVALUATION REQUIREMENTS:

Create a teacher-friendly notebook:

ai/rendering/notebooks/Rendering_V2_ControlNet_Training_Analysis.ipynb

The notebook should include:

1. Project/model configuration
2. Dataset statistics
3. Category distribution
4. Training setup
5. Training loss curves
6. Validation loss curves
7. Checkpoint comparison
8. Training time
9. VRAM usage
10. Sample generations
11. Per-category visual examples
12. Failure/challenging examples
13. V1 vs V2 comparison
14. Final recommendation

Use fixed seeds for reproducibility.

Evaluate all 8 categories:
- Ring
- Earring
- Pendant
- Necklace
- Bracelet
- Bangle
- Brooch
- Other Jewellery

For comparison, use the same:
- input conditioning image
- prompt
- seed
- resolution
- inference steps
- CFG
where practical.

Evaluate at least:
- geometry
- structural fidelity
- category correctness
- prompt adherence
- material appearance
- gemstone appearance
- fine detail
- product realism
- background quality
- hallucination/spurious components
- human/background suppression
- consistency

Use the existing V1 ControlNet as the baseline.

IMPORTANT:
The comparison must clearly distinguish:
- V1 production model
- V2 candidate model

Do not replace V1 automatically.

FILES TO CREATE/UPDATE:

1. Training implementation/configuration under the existing Rendering V2 training structure.

2. Rendering V2 training configuration, preferably:
   ai/rendering/training/configs/rendering_v2_controlnet.yaml

3. Teacher-friendly notebook:
   ai/rendering/notebooks/Rendering_V2_ControlNet_Training_Analysis.ipynb

4. Final report:
   PHASE_RENDERING_V2_CONTROLNET_TRAINING_REPORT.md

5. Keep all model outputs under a V2-specific directory, for example:
   outputs/rendering_v2_controlnet/

Never write into:
   outputs/controlnet_jewellery_300/

The report must document:
- exact base model
- exact initialization checkpoint
- dataset version/count
- hyperparameters
- hardware
- CUDA/PyTorch versions
- training duration
- checkpoints
- best checkpoint
- final checkpoint
- validation metrics
- test metrics
- V1 comparison
- per-category results
- VRAM
- inference timing
- known weaknesses
- whether V2 is ready for Rendering V2 LoRA training

QUALITY GATE:

At the end, give one of:

READY_FOR_LORA_V2
or
NEEDS_MORE_CONTROLNET_TRAINING
or
TRAINING_FAILED

Do NOT start LoRA V2 training in this phase.

Do NOT integrate the V2 model into the production application in this phase.

Do NOT commit or push.

Before finishing, show:
- git status
- git diff --stat

Then stop and wait for my review.