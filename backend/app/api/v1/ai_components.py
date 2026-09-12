import sys
from pathlib import Path
from typing import Optional
import cv2
import httpx
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

# Ensure workspace root is in sys.path for AI vision modules
_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.models.user import User

try:
    from ai.vision.inference.detector import JewelleryComponentDetector
    from ai.vision.inference.schemas import DetectionResult
except ImportError:
    # Safe fallback if optional AI dependencies are decoupled
    JewelleryComponentDetector = None
    DetectionResult = None

router = APIRouter(prefix="/ai/components", tags=["AI - Component Detection"])

# Shared cached detector instance (lazy initialized)
_detector_instance = None


def get_detector() -> Optional[JewelleryComponentDetector]:
    global _detector_instance
    if _detector_instance is None and JewelleryComponentDetector is not None:
        _detector_instance = JewelleryComponentDetector(mock_mode=False)
    return _detector_instance


@router.post(
    "/detect",
    response_model=DetectionResult if DetectionResult else dict,
    status_code=status.HTTP_200_OK,
    summary="Detect jewellery components from a sketch",
    description="Authenticates user and returns instance segmentation contours, bounding boxes, and component classifications.",
)
async def detect_jewellery_components(
    file: UploadFile = File(..., description="Jewellery sketch image (PNG, JPG, or WEBP)"),
    conf: float = Query(0.25, ge=0.0, le=1.0, description="Confidence threshold"),
    current_user: User = Depends(get_current_active_user),
):
    """Run instance segmentation on uploaded jewellery blueprint sketch."""
    valid_content_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in valid_content_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type: {file.content_type}. Accepted formats: {', '.join(valid_content_types)}",
        )

    # Read binary bytes
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        detector = get_detector()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"YOLO V2 production model unavailable: {str(exc)}",
        )

    if detector is not None and not getattr(detector, "mock_mode", False):
        # Decode image to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_np is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to decode image data. Please ensure it is a valid image file.",
            )
        try:
            result = detector.detect(img_np, conf_threshold=conf)
            return result
        except Exception as det_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference error during component detection: {str(det_err)}",
            )
    else:
        # Proxy to AI worker if local detector not available
        worker_url = f"{settings.AI_WORKER_URL.rstrip('/')}/detect"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files_payload = {"file": (file.filename or "sketch.png", contents, file.content_type or "image/png")}
                params = {"conf": str(conf)}
                resp = await client.post(worker_url, files=files_payload, data=params)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 422:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=resp.json().get("error", "Failed to decode image data."),
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"AI Vision Worker error: {resp.text}",
                    )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="YOLO V2 production model unavailable. Start the local worker or verify model weights.",
            ) from conn_err
