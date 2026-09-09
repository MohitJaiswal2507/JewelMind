"""JewelMind — Regression Test for Multi-Sample Validation Scheduler.

Verifies that DPMSolverMultistepScheduler cleanly handles multiple sequential
validation samples without state leakage or IndexError on step index bounds.
"""

import unittest
import torch
from diffusers import DPMSolverMultistepScheduler


class TestValidationSchedulerRegression(unittest.TestCase):
    """Regression test suite for scheduler state management in validation generation."""

    def test_dpm_solver_multisample_stepping(self):
        """Assert DPMSolverMultistepScheduler steps across N sequential samples without IndexError."""
        num_inference_steps = 15
        num_samples = 8
        scheduler = DPMSolverMultistepScheduler(
            num_train_timesteps=1000,
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
        )

        dummy_latents = torch.randn(1, 4, 64, 64)
        dummy_noise_pred = torch.randn(1, 4, 64, 64)

        for sample_idx in range(num_samples):
            # Reset scheduler timesteps for each sample (the fix)
            scheduler.set_timesteps(num_inference_steps)
            latents = dummy_latents.clone() * scheduler.init_noise_sigma

            steps_completed = 0
            for t in scheduler.timesteps:
                model_input = scheduler.scale_model_input(latents, t)
                output = scheduler.step(dummy_noise_pred, t, model_input)
                latents = output.prev_sample
                steps_completed += 1

            self.assertEqual(
                steps_completed,
                num_inference_steps,
                f"Sample {sample_idx} completed {steps_completed}/{num_inference_steps} steps",
            )


if __name__ == "__main__":
    unittest.main()
