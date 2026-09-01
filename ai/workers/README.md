# AI Workers Module

This module contains worker implementations for asynchronous job execution:
- `local_worker.py`: Local RTX 4060 GPU worker polling the AI queue and executing PyTorch / YOLO / XGBoost / OR-Tools tasks.
- `remote_worker.py`: Optional Hugging Face ZeroGPU / cloud worker adapter.
- `job_dispatcher.py`: Worker health check, job leasing, and status reporting logic.
