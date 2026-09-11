# ==============================================================================
# JewelMind AI Inference Worker Dockerfile
# NVIDIA CUDA GPU-Accelerated Container for ControlNet & YOLO11
# ==============================================================================

FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime AS base

WORKDIR /app

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Install system dependencies for OpenCV, PIL, and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install AI Python dependencies (excluding torch which is already preinstalled with CUDA in base image)
COPY ai/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        diffusers>=0.31.0 \
        transformers>=4.45.0 \
        accelerate>=1.0.0 \
        peft>=0.13.0 \
        safetensors>=0.4.5 \
        ultralytics>=8.3.0 \
        opencv-python-headless>=4.10.0 \
        controlnet_aux>=0.0.9 \
        pillow>=10.4.0 \
        pydantic>=2.9.0 \
        pydantic-settings>=2.5.0 \
        pyyaml>=6.0.2 \
        requests>=2.32.0 \
        httpx>=0.27.0 \
        pytest>=8.3.0

# Copy application source code (AI module, configs, scripts)
# Note: Models are mounted as runtime volumes to keep image lightweight (< 4GB)
COPY ai/ /app/ai/
COPY configs/ /app/configs/

# Create non-root user
RUN groupadd -g 10001 jewelmind && \
    useradd -u 10000 -g jewelmind -s /bin/bash -m jewelmind_ai && \
    chown -R jewelmind_ai:jewelmind /app

USER jewelmind_ai

EXPOSE 8001

# Health check verifies local HTTP inference worker is responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Production startup: run dedicated AI inference worker
CMD ["python", "ai/workers/local_worker.py"]
