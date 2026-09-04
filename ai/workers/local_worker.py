"""JewelMind Local RTX 4060 AI Inference Worker.

Lightweight dedicated HTTP server running inside the `tgpu` PyTorch/CUDA environment.
Exposes hardware-accelerated ControlNet generative diffusion and YOLO11 component detection
to the decoupled FastAPI backend over port 8001.
"""

import cgi
import io
import json
import logging
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any
import numpy as np
from PIL import Image

# Ensure workspace root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch

from ai.rendering.pipeline import JewelleryRenderingPipeline, RenderingOutOfMemoryError
from ai.rendering.schemas import RenderRequest
from ai.vision.inference.detector import JewelleryComponentDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("jewelmind.ai.worker")

# Shared cached models (lazy initialized on first request or startup)
_rendering_pipeline: JewelleryRenderingPipeline = None
_component_detector: JewelleryComponentDetector = None


def get_pipeline() -> JewelleryRenderingPipeline:
    global _rendering_pipeline
    if _rendering_pipeline is None:
        logger.info("Initializing JewelleryRenderingPipeline (SD1.5 + ControlNet)...")
        _rendering_pipeline = JewelleryRenderingPipeline()
    return _rendering_pipeline


def get_detector() -> JewelleryComponentDetector:
    global _component_detector
    if _component_detector is None:
        logger.info("Initializing JewelleryComponentDetector (YOLO11-seg)...")
        _component_detector = JewelleryComponentDetector()
    return _component_detector


class AIWorkerHandler(BaseHTTPRequestHandler):
    """HTTP Request handler for AI worker endpoints."""

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        """Health check endpoint."""
        if self.path in ("/", "/health", "/api/v1/health"):
            vram_info = {}
            if torch.cuda.is_available():
                allocated = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
                reserved = round(torch.cuda.memory_reserved() / (1024 * 1024), 2)
                device_name = torch.cuda.get_device_name(0)
                vram_info = {
                    "allocated_mb": allocated,
                    "reserved_mb": reserved,
                    "device_name": device_name,
                }

            self._send_json(200, {
                "status": "ok",
                "service": "JewelMind Local AI Worker",
                "device": "cuda" if torch.cuda.is_available() else "cpu",
                "vram": vram_info,
            })
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        """Inference execution endpoints for /render and /detect."""
        try:
            if self.path.rstrip("/") in ("/render", "/api/v1/ai/render"):
                self._handle_render()
            elif self.path.rstrip("/") in ("/detect", "/api/v1/ai/components/detect"):
                self._handle_detect()
            else:
                self._send_json(404, {"error": f"Endpoint {self.path} not found"})
        except RenderingOutOfMemoryError as oom:
            logger.error("GPU VRAM OOM during render: %s", oom)
            self._send_json(507, {"error": "GPU memory limit exceeded during diffusion rendering."})
        except Exception as exc:
            logger.exception("Worker execution failure: %s", exc)
            self._send_json(500, {"error": f"Internal AI Worker error: {str(exc)}"})

    def _parse_multipart(self):
        """Parse multipart form-data payload safely."""
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError(f"Expected multipart/form-data, got {content_type}")

        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
        }
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=environ,
            keep_blank_values=True,
        )
        return form

    def _handle_render(self):
        """Execute ControlNet generative diffusion."""
        form = self._parse_multipart()

        if "file" not in form:
            self._send_json(400, {"error": "Missing sketch 'file' in request form."})
            return

        file_item = form["file"]
        file_bytes = file_item.file.read()

        try:
            pil_image = Image.open(io.BytesIO(file_bytes))
            pil_image.load()
        except Exception as e:
            self._send_json(422, {"error": f"Failed to decode image: {str(e)}"})
            return

        # Parse form parameters with safe defaults
        category = form.getvalue("category", None)
        prompt = form.getvalue("prompt", None)
        negative_prompt = form.getvalue("negative_prompt", None)
        material = form.getvalue("material", "18k yellow gold")
        gemstone = form.getvalue("gemstone", "round brilliant diamond")
        control_type = form.getvalue("control_type", "lineart")

        try:
            control_strength = float(form.getvalue("control_strength", "1.0"))
            steps = int(form.getvalue("steps", "20"))
            guidance_scale = float(form.getvalue("guidance_scale", "7.5"))
            seed_val = form.getvalue("seed", None)
            seed = int(seed_val) if seed_val not in (None, "", "null") else None
            width = int(form.getvalue("width", "512"))
            height = int(form.getvalue("height", "512"))
        except ValueError as ve:
            self._send_json(422, {"error": f"Invalid numerical parameter: {str(ve)}"})
            return

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
        )

        pipeline = get_pipeline()
        logger.info("Starting render job: category=%s, material=%s, gemstone=%s, steps=%d, seed=%s",
                    category, material, gemstone, steps, seed)
        _, result = pipeline.render(pil_image, request=req)
        
        # Return dict serialization of RenderResult
        self._send_json(200, result.model_dump())

    def _handle_detect(self):
        """Execute YOLO11 component detection."""
        import cv2

        form = self._parse_multipart()
        if "file" not in form:
            self._send_json(400, {"error": "Missing sketch 'file' in request form."})
            return

        file_item = form["file"]
        file_bytes = file_item.file.read()
        conf_str = form.getvalue("conf", "0.25")
        try:
            conf = float(conf_str)
        except ValueError:
            conf = 0.25

        nparr = np.frombuffer(file_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_np is None:
            self._send_json(422, {"error": "Failed to decode image data."})
            return

        detector = get_detector()
        logger.info("Executing YOLO component detection (conf=%.2f)...", conf)
        result = detector.detect(img_np, conf_threshold=conf)
        self._send_json(200, result.model_dump())


def run_worker(host: str = "127.0.0.1", port: int = 8001):
    """Start the AI Worker HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, AIWorkerHandler)
    logger.info("==================================================")
    logger.info("JewelMind Local AI Worker started on http://%s:%d", host, port)
    logger.info("PyTorch: %s | CUDA: %s | Device: %s",
                torch.__version__,
                torch.cuda.is_available(),
                torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
    logger.info("Ready to process GPU diffusion rendering and YOLO segmentation.")
    logger.info("==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down AI worker...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.getenv("AI_WORKER_PORT", "8001"))
    host = os.getenv("AI_WORKER_HOST", "127.0.0.1")
    run_worker(host=host, port=port)
