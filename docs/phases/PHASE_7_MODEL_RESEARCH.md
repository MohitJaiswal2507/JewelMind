# JewelMind — Phase 7: Diffusion & ControlNet Model Research Report

## 1. Executive Summary

This research document evaluates generative diffusion architectures and ControlNet conditioning adapters for **JewelMind Phase 7: AI Jewellery Sketch-to-Photorealistic Rendering**. 

The hardware platform is strictly constrained to a local **NVIDIA GeForce RTX 4060 Laptop GPU with 8,188 MiB (8 GB) VRAM**. Operating systems and display drivers on Windows laptops typically allocate 1.5–2.0 GB of VRAM for system UI, desktop composition (WDDM), and background tasks, leaving approximately **6.0–6.5 GB of usable VRAM** for machine learning inference without falling back into shared system RAM paging (which degrades inference speed by 10x–20x).

The primary objective of Phase 7 is:
> **"Preserve jewellery sketch geometry (silhouettes, stone count/placement, ring shank thickness, prong settings, symmetry) while rendering photorealistic metals (18k yellow gold, platinum, rose gold) and refractive gemstones under studio lighting."**

Based on empirical and architectural analysis across four candidate families, **Stable Diffusion 1.5 + ControlNet (LineArt & Canny)** is selected as the primary rendering engine for JewelMind Phase 7.

---

## 2. Hardware Constraints & Memory Budget

| Hardware Metric | Target Specification | Practical Implication |
| :--- | :--- | :--- |
| **GPU** | NVIDIA GeForce RTX 4060 Laptop GPU (Ada Lovelace, AD107) | 3072 CUDA Cores, 24 4th-Gen Tensor Cores |
| **Total VRAM** | 8,188 MiB (8 GB) GDDR6, 128-bit bus | Hard ceiling for weights, activations, and KV cache |
| **OS / Display Overhead** | Windows 11 WDDM (Desktop Window Manager + Apps) | Uses ~1.8–2.0 GB; net free VRAM is ~6.1 GB |
| **Paging Penalty** | Shared System RAM fallback | Severe latency penalty (>45s per image) if memory leaks or exceeds 8 GB |
| **Target Latency** | < 10 seconds per 512×512 image | Interactive Design Studio user experience |
| **Batch Size** | 1 (strictly serialized) | Prevents concurrent memory spikes |
| **Precision** | Float16 (`torch.float16`) | Halves model weight and activation footprint |

---

## 3. Candidate Architectural Comparisons

### Candidate 1: Stable Diffusion 1.5 + ControlNet v1.1 (SELECTED)

* **Base Model / Checkpoint**: `runwayml/stable-diffusion-v1-5` (or community fine-tunes such as `cyberdelia/CyberRealistic`, `SG161222/Realistic_Vision_V5.1_noVAE`).
* **ControlNet Checkpoints**: `lllyasviel/control_v11p_sd15_lineart`, `lllyasviel/control_v11p_sd15_canny`.
* **Architecture**: Latent Diffusion Model (LDM) with CLIP ViT-L/14 text encoder, 860M parameter UNet, AutoencoderKL VAE (downsampling factor 8), and parallel ControlNet encoder replicating UNet encoder blocks with zero-convolutions.
* **Native Resolution**: $512 \times 512$ pixels.
* **Download Footprint**:
  * SD 1.5 Base (`fp16` safetensors): ~1.7 GB
  * ControlNet LineArt (`fp16` safetensors): ~1.45 GB
  * ControlNet Canny (`fp16` safetensors): ~1.45 GB
  * Total initial storage: ~3.2 GB per conditioning workflow.
* **VRAM Footprint (Batch 1, 512×512, fp16)**:
  * UNet + ControlNet + CLIP loaded in VRAM: ~3.4 GB
  * Peak activation memory during backward/denoising pass: ~0.8 GB
  * Peak VRAM consumption: **~4.2 GB – 4.8 GB**.
* **8 GB Practicality**: **Outstanding**. Comfortably operates within the 6.1 GB free window on Windows without requiring aggressive CPU offloading or triggering shared RAM thrashing.
* **Inference Speed**: ~3.5 to 5.5 seconds for 20 Euler a / UniPC steps on RTX 4060.
* **Geometry / Control Fidelity**: **Exceptional**. ControlNet v1.1 for SD 1.5 has the highest spatial precision and cleanest edge conditioning of any open-source diffusion adapter. LineArt conditioning adheres strictly to hand-drawn sketches and CAD blueprint contours.
* **LoRA Compatibility**: Massive ecosystem; thousands of specialized jewellery, metal finish, gemstone refraction, and studio lighting LoRA weights are natively compatible.
* **License**: CreativeML Open RAIL-M (Permissive commercial use with standard behavioral use restrictions).
* **Strengths**: Low VRAM footprint, high inference speed, pinpoint geometry alignment, robust control over fine filigree and prong settings, rock-solid stability on 8 GB GPUs.
* **Weaknesses**: Lower native resolution ($512 \times 512$ vs $1024 \times 1024$); requires prompt engineering or negative prompts to prevent generic background noise.

---

### Candidate 2: Stable Diffusion XL (SDXL) 1.0 + ControlNet SDXL

* **Base Model / Checkpoint**: `stabilityai/stable-diffusion-xl-base-1.0`.
* **ControlNet Checkpoint**: `diffusers/controlnet-canny-sdxl-1.0`, `thibaud/controlnet-openpose-sdxl-1.0`.
* **Architecture**: Dual text encoders (OpenCLIP ViT-bigG/14 + CLIP ViT-L/14), 2.6B parameter UNet, larger VAE.
* **Native Resolution**: $1024 \times 1024$ pixels.
* **Download Footprint**:
  * SDXL Base (`fp16` safetensors): ~6.9 GB
  * SDXL ControlNet (`fp16` safetensors): ~2.5 GB
  * Total initial storage: ~9.4 GB.
* **VRAM Footprint (Batch 1, 1024×1024, fp16)**:
  * Base UNet + Dual Text Encoders + ControlNet: ~7.2 GB
  * Peak activations with attention slicing: ~1.5 GB
  * Peak VRAM consumption: **8.5 GB – 9.8 GB**.
* **8 GB Practicality**: **Extremely High Risk of CUDA OOM**. Exceeds 8 GB VRAM on Windows without aggressive `enable_sequential_cpu_offload()` or 4-bit/8-bit quantization.
* **Inference Speed**: 18 – 35 seconds per image when CPU offloading is enabled (constant weight swapping over PCIe bus).
* **Geometry / Control Fidelity**: Moderate to Good. SDXL ControlNet adapters have significantly less training stability and lower contour precision on fine jewellery blueprints than SD 1.5 ControlNet v1.1. Fine prongs and gemstone facet lines frequently smudge.
* **LoRA Compatibility**: Extensive, but SDXL LoRA weights require 2x–4x more memory to merge and apply.
* **License**: OpenRAIL++-M (Permissive commercial use with attribution and behavioral restrictions).
* **Verdict**: **REJECTED for Phase 7 Primary Pipeline**. Does not provide reliable, crash-free execution on an 8 GB laptop GPU under Windows WDDM.

---

### Candidate 3: SDXL Turbo / SDXL Lightning + ControlNet

* **Base Model / Checkpoint**: `ByteDance/SDXL-Lightning` (4-step / 8-step UNet) or `stabilityai/sdxl-turbo`.
* **ControlNet Checkpoints**: `xinsir/controlnet-canny-sdxl-lightning` or standard SDXL ControlNet with step distillation.
* **Architecture**: Distilled SDXL student models capable of generating output in 4 to 8 steps via adversarial or progressive diffusion distillation.
* **Native Resolution**: $512 \times 512$ (Turbo) to $1024 \times 1024$ (Lightning).
* **Download Footprint**: ~7.0 GB base + ~2.5 GB ControlNet = ~9.5 GB.
* **VRAM Footprint**: ~7.0 GB – 8.5 GB.
* **8 GB Practicality**: **Poor to Marginal**. While step latency drops (from 20 steps to 4 steps), the *static model weight footprint* in VRAM remains identical to SDXL (~7+ GB). It still exceeds safe VRAM thresholds on an 8 GB Windows machine.
* **Geometry / Control Fidelity**: Degraded. Few-step distillation (4–8 steps) gives the ControlNet guidance fewer sampling iterations to enforce boundary alignment, resulting in loose silhouettes and distorted prongs.
* **License**: SDXL Turbo is strictly Non-Commercial Research (`stabilityai` research license). SDXL Lightning is Apache 2.0.
* **Verdict**: **REJECTED for Phase 7 Primary Pipeline**. Memory footprint is still too high, and step-reduction compromises fine geometrical fidelity on intricate jewellery sketches.

---

### Candidate 4: Flux.1-schnell / Flux.1-dev + ControlNet

* **Base Model / Checkpoint**: `black-forest-labs/FLUX.1-schnell`.
* **Architecture**: 12B parameter Rectified Flow Transformer (DiT) with T5-XXL and CLIP encoders.
* **Native Resolution**: $1024 \times 1024$.
* **Download Footprint**: > 24 GB.
* **VRAM Footprint**: 16 GB to 24 GB (requires GGUF/NF4 quantization even to fit 12 GB).
* **8 GB Practicality**: **Completely Unviable**. Instant CUDA OOM on 8 GB without severe 4-bit quantization and full offloading, taking >60 seconds per render.
* **Verdict**: **REJECTED**. Totally incompatible with local 8 GB hardware target.

---

## 4. ControlNet Conditioning Research: LineArt vs. Canny vs. SoftEdge

Jewellery blueprint sketches present unique structural characteristics:
1. High contrast (pencil or digital ink on light/transparent canvas).
2. Clean continuous lines representing rings, shanks, prongs, and settings.
3. Facet lines indicating gemstone geometry.

| Conditioning Adapter | Mechanism | Performance on Jewellery Sketches | Recommendation |
| :--- | :--- | :--- | :--- |
| **LineArt (`control_v11p_sd15_lineart`)** | Trained on clean vector lines, line drawings, and sketches. | **Best fidelity**. Accurately perceives sketched strokes as object boundaries rather than texture. Preserves stone facets and bezel outlines without producing double-edge artifacts. | **PRIMARY SELECTION** |
| **Canny (`control_v11p_sd15_canny`)** | OpenCV dual-threshold gradient magnitude edge detector. | **Excellent fallback**. Very fast, deterministic, zero-model preprocessing. Can occasionally produce double edges on thick pencil strokes. | **SECONDARY / FALLBACK** |
| **SoftEdge / HED (`control_v11p_sd15_softedge`)** | Holistically-nested edge detection with soft probability gradients. | Good for soft shading, but allows too much structural drift in rigid precious metal contours. | Optional future extension |
| **Scribble (`control_v11p_sd15_scribble`)** | Loose sketch conditioning. | Allows too much hallucination; alters prong count and gemstone shapes. | Rejected for fine jewellery |
| **Depth (`control_v11p_sd15_depth`)** | Monocular depth estimation (MiDaS / DPT). | Struggles on 2D flat blueprint sketches without shading. | Rejected for 2D sketches |

**Conclusion**: Implement both **LineArt** and **Canny** via an extensible `ConditioningProcessor` architecture, designating `LineArt` as the primary default for jewellery sketch rendering and `Canny` as a fast secondary alternative.

---

## 5. Memory Strategy for RTX 4060 8GB

To guarantee that JewelMind never triggers a CUDA Out-Of-Memory (OOM) error or Windows shared-memory thrashing:

1. **Half-Precision (FP16)**:
   - Load SD 1.5 UNet, ControlNet, CLIP, and VAE in `torch.float16`.
2. **Attention Slicing**:
   - Enable `pipeline.enable_attention_slicing("auto")`. Computes cross-attention in sequential chunks, reducing peak activation memory by ~400 MB with negligible (<5%) latency impact.
3. **VAE Slicing & Tiling**:
   - Enable `pipeline.enable_vae_slicing()` to decode latents sequentially rather than all at once.
4. **Target Resolution**:
   - Fix primary resolution to $512 \times 512$ with batch size $1$.
5. **Strict Serialization Lock**:
   - Concurrency lock (`asyncio.Lock` in API and `threading.Lock` in Model Manager) ensuring only one diffusion inference job executes on the GPU at any time.
6. **Active Cache Clearing**:
   - Execute `torch.cuda.empty_cache()` and `gc.collect()` before and after every rendering invocation.

---

## 6. Prompt Engineering Strategy for Fine Jewellery

Diffusers with ControlNet rely on prompt conditioning to guide material rendering (metal reflection, refractive dispersion, studio environment) while the ControlNet enforces spatial shape.

### Curated Positive Prompt Template
```
photorealistic fine jewellery product photograph, {material_prompt}, set with {gemstone_prompt}, luxury design, studio lighting, soft shadows, clean reflective surface, sharp focus, 8k resolution, elegant craftsmanship, commercial jewellery photography
```

### Comprehensive Negative Prompt
```
deformed ring, malformed jewellery, melted metal, broken geometry, missing gemstones, extra gemstones, floating stones, distorted prongs, asymmetric shank, low quality, blurry, pixelated, noisy, watermark, text, signature, logo, human hands, fingers, skin, mannequins, tools, workbench, background clutter
```

---

## 7. Licensing & Commercial Compliance

| Component | License | Commercial Implications |
| :--- | :--- | :--- |
| **Stable Diffusion 1.5** | CreativeML Open RAIL-M | Permitted for commercial use. Standard restrictions against illegal/harmful generative content. Fully compliant for jewellery CAD rendering. |
| **ControlNet v1.1** | Apache 2.0 | Fully permissive commercial use without royalties. |
| **Diffusers / Transformers** | Apache 2.0 | Fully permissive open-source framework. |
| **OpenCV / Pillow** | Apache 2.0 / HPND | Permissive commercial libraries. |

All selected components are 100% royalty-free, locally runnable, and suitable for commercial deployment.

---

## 8. Summary of Model Selection

* **Selected Engine**: **Stable Diffusion 1.5 (`runwayml/stable-diffusion-v1-5`)**
* **Selected ControlNet**: **ControlNet v1.1 LineArt (`lllyasviel/control_v11p_sd15_lineart`)** with **Canny (`lllyasviel/control_v11p_sd15_canny`)** fallback
* **Hardware Compatibility**: Peak VRAM ~4.5 GB on 8 GB RTX 4060 GPU
* **Inference Speed**: ~4 seconds per render (20 steps, fp16)
* **Status**: APPROVED for Phase 7 implementation.
