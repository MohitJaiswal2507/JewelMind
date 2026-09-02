"""Unit Tests for CUDA and GPU Device Detection on RTX 4060."""

import pytest
import torch


def test_cuda_availability():
    """Verify PyTorch detects NVIDIA CUDA capability."""
    assert torch.cuda.is_available(), "CUDA is not available in test environment"


def test_rtx_4060_device_name():
    """Verify GPU device identifies as RTX 4060."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available on this host")

    device_name = torch.cuda.get_device_name(0)
    assert "RTX 4060" in device_name or "GeForce" in device_name, f"Unexpected GPU device: {device_name}"


def test_vram_capacity_check():
    """Verify GPU total memory is >= 6 GB (RTX 4060 typically has ~8 GB)."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available on this host")

    total_mem_bytes = torch.cuda.get_device_properties(0).total_memory
    total_mem_gb = total_mem_bytes / (1024**3)
    assert total_mem_gb >= 6.0, f"Expected at least 6 GB VRAM, found {total_mem_gb:.2f} GB"


def test_cuda_tensor_allocation():
    """Verify simple forward pass and tensor memory allocation on device 0."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available on this host")

    device = torch.device("cuda:0")
    x = torch.ones((100, 100), device=device)
    y = x @ x
    assert y.is_cuda
    assert y.sum().item() == 1000000.0
