"""AI Generative Jewellery Rendering API Endpoints.

Provides authenticated inference service for sketch-to-photorealistic rendering
conditioned on sketches via ControlNet + Stable Diffusion.
"""

import io
import sys
import uuid
from pathlib import Path
from typing import Optional, Union
import cv2
import httpx
import numpy as np
from PIL import Image
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

# Ensure workspace root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.design import Design
from app.services.storage_service import storage_service

try:
    from ai.rendering.config import DEFAULT_OUTPUT_DIR
    from ai.rendering.schemas import RenderRequest, RenderResult
except ImportError:
    DEFAULT_OUTPUT_DIR = str(_ROOT / "outputs" / "rendering")
    RenderRequest = None
    RenderResult = None

try:
    from ai.rendering.pipeline import JewelleryRenderingPipeline, RenderingOutOfMemoryError
except ImportError:
    JewelleryRenderingPipeline = None
    RenderingOutOfMemoryError = RuntimeError

router = APIRouter(prefix="/ai/render", tags=["AI - Generative Rendering"])

# Cached pipeline instance (lazy initialized)
_pipeline_instance = None


def get_rendering_pipeline() -> Optional[JewelleryRenderingPipeline]:
    global _pipeline_instance
    if _pipeline_instance is None and JewelleryRenderingPipeline is not None:
        _pipeline_instance = JewelleryRenderingPipeline()
    return _pipeline_instance


import base64

@router.post(
    "",
    response_model=RenderResult if RenderResult else dict,
    status_code=status.HTTP_200_OK,
    summary="Render jewellery photorealistic image from sketch",
    description="Transforms an uploaded jewellery blueprint sketch or sketch URL into a photorealistic render preserving geometry.",
)
async def render_jewellery_sketch(
    file: Optional[UploadFile] = File(None, description="Jewellery sketch blueprint (PNG, JPG, or WEBP)"),
    sketch_url: Optional[str] = Form(None, description="Direct URL or data URL of jewellery sketch"),
    category: Optional[str] = Form(None, description="Controlled jewellery category ('ring', 'earring', 'pendant', 'necklace', 'bracelet', 'bangle', 'brooch', 'other')"),
    design_id: Optional[uuid.UUID] = Form(None, description="Optional design ID to link and persist the render directly"),
    prompt: Optional[str] = Form(None, description="Optional custom prompt additions"),
    negative_prompt: Optional[str] = Form(None, description="Optional custom negative prompt overrides"),
    material: str = Form("18k yellow gold", description="Base jewellery precious metal"),
    gemstone: str = Form("round brilliant diamond", description="Gemstone specification"),
    control_type: str = Form("lineart", description="Conditioning adapter: 'lineart' or 'canny'"),
    control_strength: float = Form(1.0, ge=0.1, le=1.0, description="ControlNet guidance scale"),
    steps: int = Form(20, ge=10, le=50, description="Denoising steps"),
    guidance_scale: float = Form(7.5, ge=1.0, le=15.0, description="Classifier-Free Guidance (CFG) scale"),
    seed: Optional[int] = Form(None, ge=0, description="Seed for deterministic generation"),
    width: int = Form(512, ge=256, le=768, description="Output image width in pixels"),
    height: int = Form(512, ge=256, le=768, description="Output image height in pixels"),
    structured_design: Optional[str] = Form(None, description="Optional Gemini structured design understanding JSON for contextual telemetry"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Execute ControlNet conditioned diffusion generation on an uploaded jewellery sketch or sketch URL."""
    # Validate resolution multiple of 8
    if width % 8 != 0 or height % 8 != 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Resolution ({width}x{height}) must have dimensions divisible by 8.",
        )

    # Validate design existence and ownership upfront if design_id is provided
    target_design = None
    if design_id:
        target_design = db.query(Design).filter(Design.id == design_id, Design.user_id == current_user.id).first()
        if not target_design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Design with id '{design_id}' was not found or access is denied.",
            )

    contents: Optional[bytes] = None
    filename = "sketch.png"
    content_type = "image/png"

    # 1. Read binary bytes from multipart file upload if present
    if file is not None and file.filename:
        filename = file.filename
        content_type = file.content_type or "image/png"
        valid_content_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if content_type not in valid_content_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file type: {content_type}. Accepted formats: {', '.join(valid_content_types)}",
            )
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded sketch file is empty (0 bytes).",
            )

    # 2. Read from sketch_url if no file provided
    if not contents and sketch_url:
        if sketch_url.startswith("data:"):
            try:
                _, encoded = sketch_url.split(",", 1)
                contents = base64.b64decode(encoded)
            except Exception as b64_err:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid base64 data URL for sketch image.",
                ) from b64_err
        elif sketch_url.startswith("http://") or sketch_url.startswith("https://"):
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(sketch_url)
                    if resp.status_code == 200:
                        contents = resp.content
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Failed to fetch remote sketch image (HTTP {resp.status_code}).",
                        )
            except HTTPException:
                raise
            except Exception as dl_err:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to download remote sketch image: {str(dl_err)}",
                ) from dl_err

    # 3. Fallback to target_design sketch_image_url
    if not contents and target_design and target_design.sketch_image_url:
        src = target_design.sketch_image_url
        if src.startswith("http://") or src.startswith("https://"):
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(src)
                    if resp.status_code == 200:
                        contents = resp.content
            except Exception:
                pass

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No sketch image provided. Please upload a sketch file or provide a sketch image URL.",
        )

    # Decode image using PIL
    try:
        pil_image = Image.open(io.BytesIO(contents))
        pil_image.load()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to decode image data. Please upload a valid image file.",
        ) from exc

    # Construct request with validation handling
    try:
        req = RenderRequest(
            category=category,
            prompt=prompt,
            negative_prompt=negative_prompt,
            material=material,
            gemstone=gemstone,
            control_type=control_type,
            control_strength=control_strength,
            steps=steps,
            guidance_scale=guidance_scale,
            seed=seed,
            width=width,
            height=height,
            structured_design=structured_design,
        )
    except Exception as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid render parameters: {str(val_err)}",
        ) from val_err

    pipeline = get_rendering_pipeline()
    rendered_image_bytes = None
    render_dict = None

    if pipeline is not None:
        try:
            rendered_pil, result = pipeline.render(pil_image, request=req)
            if hasattr(rendered_pil, "save"):
                buf = io.BytesIO()
                rendered_pil.save(buf, format="PNG")
                rendered_image_bytes = buf.getvalue()
            render_dict = result.model_dump() if hasattr(result, "model_dump") else (dict(result) if isinstance(result, dict) else {})
            if structured_design and isinstance(render_dict, dict):
                render_dict["structured_design"] = structured_design
        except RenderingOutOfMemoryError as oom_err:
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail="Rendering exceeded available GPU memory. Try a lower resolution or wait for current GPU jobs to finish.",
            ) from oom_err
        except RuntimeError as run_err:
            if "busy" in str(run_err).lower():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rendering engine is busy processing another job. Please retry shortly.",
                ) from run_err
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rendering pipeline failed: {str(run_err)}",
            ) from run_err
    else:
        # Proxy request to dedicated AI Worker running in tgpu environment
        worker_url = f"{settings.AI_WORKER_URL.rstrip('/')}/render"
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                files_payload = {"file": (filename, contents, content_type)}
                form_payload = {
                    "category": category or "",
                    "prompt": prompt or "",
                    "negative_prompt": negative_prompt or "",
                    "material": material,
                    "gemstone": gemstone,
                    "control_type": control_type,
                    "control_strength": str(control_strength),
                    "steps": str(steps),
                    "guidance_scale": str(guidance_scale),
                    "seed": str(seed) if seed is not None else "",
                    "width": str(width),
                    "height": str(height),
                    "structured_design": structured_design or "",
                }
                resp = await client.post(worker_url, files=files_payload, data=form_payload)
                if resp.status_code == 200:
                    render_dict = resp.json()
                    # Read generated PNG from disk if available
                    out_name = Path(render_dict.get("output_url", "")).name
                    local_target = Path(DEFAULT_OUTPUT_DIR) / out_name
                    if local_target.exists() and local_target.is_file():
                        rendered_image_bytes = local_target.read_bytes()
                elif resp.status_code == 507:
                    raise HTTPException(
                        status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                        detail=resp.json().get("error", "GPU VRAM exceeded during rendering."),
                    )
                elif resp.status_code == 422:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=resp.json().get("error", "Invalid rendering parameters."),
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"AI Worker returned error: {resp.text}",
                    )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI rendering worker is offline. Start the local RTX 4060 worker.",
            ) from conn_err

    # Upload rendered image to Supabase Storage if image bytes available
    if rendered_image_bytes and render_dict:
        try:
            public_supabase_url, _ = await storage_service.upload_rendered_image(
                file_bytes=rendered_image_bytes,
                user_id=current_user.id,
                design_id=design_id,
            )
            render_dict["output_url"] = public_supabase_url

            # Automatically persist to design if design_id was provided
            if design_id:
                design = db.query(Design).filter(Design.id == design_id, Design.user_id == current_user.id).first()
                if design:
                    design.rendered_image_url = public_supabase_url
                    design.status = "ready"
                    db.commit()
                    db.refresh(design)
        except Exception as storage_err:
            # Fallback to local output URL if storage upload failed
            pass

    return render_dict


@router.get(
    "/outputs/{filename}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve generated jewellery render",
    description="Fetches a generated output image file by its unique identifier.",
)
async def get_rendered_image(filename: str):
    """Serve rendered image without exposing filesystem directory paths."""
    # Sanitize filename against directory traversal
    safe_filename = Path(filename).name
    target_path = Path(DEFAULT_OUTPUT_DIR) / safe_filename

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendered image not found or expired.",
        )

    return FileResponse(path=str(target_path), media_type="image/png")
