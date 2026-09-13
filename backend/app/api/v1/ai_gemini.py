"""FastAPI Router for Gemini Multimodal Design Understanding & Prompt Enhancement.

Endpoints:
- POST /api/v1/ai/gemini/analyze-design
- POST /api/v1/ai/gemini/enhance-prompt
"""

import base64
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import httpx

from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.ai import (
    AnalyzeDesignResponse,
    EnhancePromptRequest,
    EnhancePromptResponse,
    YoloGroundingContext,
)
from app.services.gemini_design_service import get_gemini_design_service

router = APIRouter(prefix="/ai/gemini", tags=["AI - Gemini Design Understanding"])


@router.post(
    "/analyze-design",
    response_model=AnalyzeDesignResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze jewellery sketch or image with Gemini Vision",
    description=(
        "Analyzes an uploaded jewellery sketch or photo with Google Gemini Vision. "
        "Extracts structured specifications (metal, gemstones, prongs, shank) "
        "and compiles a photorealistic diffusion prompt preserving explicit user intent."
    ),
)
async def analyze_jewellery_design(
    file: Optional[UploadFile] = File(None, description="Optional sketch or photograph binary file"),
    image_url: Optional[str] = Form(None, description="Optional public URL or Supabase storage URL"),
    image_base64: Optional[str] = Form(None, description="Optional base64-encoded image string"),
    user_prompt: Optional[str] = Form(None, description="Optional artisan design notes or custom constraints"),
    yolo_category: Optional[str] = Form(None, description="Optional category grounding from YOLO V2"),
    yolo_confidence: Optional[float] = Form(None, description="Optional YOLO V2 detection confidence"),
    source_blueprint_category: Optional[str] = Form(None, description="Optional category of source blueprint sketch"),
    user_selected_category: Optional[str] = Form(None, description="Optional user manual selection from UI dropdown"),
    current_user: User = Depends(get_current_active_user),
):
    """Execute multimodal jewellery design analysis."""
    image_bytes: Optional[bytes] = None
    mime_type = "image/png"

    # 1. Read binary bytes if file uploaded
    if file and file.filename:
        valid_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if file.content_type and file.content_type.lower() not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file type: {file.content_type}. Accepted formats: {', '.join(valid_types)}",
            )
        image_bytes = await file.read()
        mime_type = file.content_type or "image/png"

    # 2. Decode base64 if provided and no file
    elif image_base64:
        try:
            raw_b64 = image_base64
            if "base64," in raw_b64:
                header, raw_b64 = raw_b64.split("base64,", 1)
                if "image/jpeg" in header or "image/jpg" in header:
                    mime_type = "image/jpeg"
                elif "image/webp" in header:
                    mime_type = "image/webp"
            image_bytes = base64.b64decode(raw_b64)
        except Exception as b64_err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid base64 encoded image string.",
            ) from b64_err

    # 3. Download remote URL if provided and no bytes yet
    elif image_url and (image_url.startswith("http://") or image_url.startswith("https://")):
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(image_url)
                if resp.status_code == 200:
                    image_bytes = resp.content
                    ct = resp.headers.get("Content-Type", "image/png")
                    if "jpeg" in ct or "jpg" in ct:
                        mime_type = "image/jpeg"
                    elif "webp" in ct:
                        mime_type = "image/webp"
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Failed to fetch remote image URL (HTTP {resp.status_code}).",
                    )
        except HTTPException:
            raise
        except Exception as dl_err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error downloading remote image: {str(dl_err)}",
            ) from dl_err

    # Build YOLO context if provided
    yolo_context: Optional[YoloGroundingContext] = None
    if yolo_category and yolo_category.strip():
        yolo_context = YoloGroundingContext(
            detected_category=yolo_category.strip(),
            confidence=yolo_confidence if yolo_confidence is not None else 0.85,
        )

    service = get_gemini_design_service()
    try:
        response = await service.analyze_design(
            image_bytes=image_bytes,
            user_prompt=user_prompt,
            yolo_context=yolo_context,
            image_mime_type=mime_type,
            source_blueprint_category=source_blueprint_category,
            user_selected_category=user_selected_category,
        )
        return response
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Design analysis service error: {str(err)}",
        ) from err


@router.post(
    "/enhance-prompt",
    response_model=EnhancePromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Enhance jewellery prompt with Gemini AI",
    description=(
        "Refines an artisan's prompt with precision gemological terminology and diffusion anchors. "
        "Strictly preserves explicit user constraints (metal, stone, cut, shank) while elevating aesthetics."
    ),
)
async def enhance_jewellery_prompt(
    payload: EnhancePromptRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Execute standalone natural-language prompt enhancement."""
    image_bytes: Optional[bytes] = None
    mime_type = "image/png"

    if payload.image_base64:
        try:
            raw_b64 = payload.image_base64
            if "base64," in raw_b64:
                header, raw_b64 = raw_b64.split("base64,", 1)
                if "image/jpeg" in header or "image/jpg" in header:
                    mime_type = "image/jpeg"
                elif "image/webp" in header:
                    mime_type = "image/webp"
            image_bytes = base64.b64decode(raw_b64)
        except Exception:
            pass
    elif payload.image_url and (payload.image_url.startswith("http://") or payload.image_url.startswith("https://")):
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(payload.image_url)
                if resp.status_code == 200:
                    image_bytes = resp.content
                    ct = resp.headers.get("Content-Type", "image/png")
                    if "jpeg" in ct or "jpg" in ct:
                        mime_type = "image/jpeg"
                    elif "webp" in ct:
                        mime_type = "image/webp"
        except Exception:
            pass

    yolo_context: Optional[YoloGroundingContext] = None
    if payload.yolo_category and payload.yolo_category.strip():
        yolo_context = YoloGroundingContext(
            detected_category=payload.yolo_category.strip(),
            confidence=payload.yolo_confidence if payload.yolo_confidence is not None else 0.85,
        )

    service = get_gemini_design_service()
    try:
        response = await service.enhance_prompt(
            user_prompt=payload.user_prompt,
            image_bytes=image_bytes,
            yolo_context=yolo_context,
            image_mime_type=mime_type,
            source_blueprint_category=payload.source_blueprint_category,
            user_selected_category=payload.user_selected_category,
        )
        return response
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prompt enhancement service error: {str(err)}",
        ) from err
