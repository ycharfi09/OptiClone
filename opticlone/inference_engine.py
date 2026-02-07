"""
inference_engine.py — LuxTTS model wrapper for OptiClone.

Handles model loading, reference-audio encoding, and speech generation.
Designed to be called from the UI layer with simple, thread-safe methods.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

# Ensure HF hub cache points to the local cache directory
os.environ.setdefault("HF_HUB_CACHE", os.path.expanduser(r"~\.cache\huggingface\hub"))
from typing import Optional

import numpy as np
import torch

from opticlone.config import (
    DEFAULT_NUM_STEPS,
    DEFAULT_REF_DURATION,
    DEFAULT_RETURN_SMOOTH,
    DEFAULT_RMS,
    DEFAULT_SPEED,
    DEFAULT_T_SHIFT,
    MODEL_REPO,
    SAMPLE_RATE,
)

logger = logging.getLogger("opticlone.engine")


class InferenceEngine:
    """Thin wrapper around the LuxTTS model.

    Usage
    -----
    >>> engine = InferenceEngine(device="cuda")
    >>> engine.load_model()
    >>> engine.set_reference("speaker.wav")
    >>> wav_np = engine.generate("Hello, world!")
    """

    def __init__(self, device: Optional[str] = None) -> None:
        self._device = device or self._detect_device()
        self._model = None
        self._encoded_prompt = None
        self._ref_path: Optional[str] = None
        logger.info("InferenceEngine initialised  (device=%s)", self._device)

    # ── Device detection ─────────────────────────────────────────
    @staticmethod
    def _detect_device() -> str:
        """Pick the best available device: CUDA ▸ MPS ▸ CPU."""
        if torch.cuda.is_available():
            return "cuda"
        try:
            if torch.backends.mps.is_available():
                return "mps"
        except AttributeError:
            pass
        return "cpu"

    @property
    def device(self) -> str:
        return self._device

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def has_reference(self) -> bool:
        return self._encoded_prompt is not None

    @property
    def reference_path(self) -> Optional[str]:
        return self._ref_path

    # ── Model lifecycle ──────────────────────────────────────────
    def load_model(self) -> None:
        """Download (if needed) and load the LuxTTS model."""
        if self._model is not None:
            logger.info("Model already loaded — skipping.")
            return

        logger.info("Loading LuxTTS model from %s …", MODEL_REPO)
        t0 = time.perf_counter()

        # Import here so startup stays fast when just importing the module.
        from zipvoice.luxvoice import LuxTTS  # type: ignore[import-untyped]

        kwargs = {"device": self._device}
        if self._device == "cpu":
            kwargs["threads"] = 2

        self._model = LuxTTS(MODEL_REPO, **kwargs)
        dt = time.perf_counter() - t0
        logger.info("Model loaded in %.1f s", dt)

    def unload_model(self) -> None:
        """Release model from memory / VRAM."""
        self._model = None
        self._encoded_prompt = None
        self._ref_path = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Model unloaded.")

    # ── Reference audio ──────────────────────────────────────────
    def set_reference(
        self,
        audio_path: str | Path,
        *,
        duration: float = DEFAULT_REF_DURATION,
        rms: float = DEFAULT_RMS,
    ) -> None:
        """Encode a reference audio clip for voice cloning.

        Parameters
        ----------
        audio_path : path to a .wav or .mp3 file (≥ 3 s recommended).
        duration   : seconds of audio to encode (lower = faster).
        rms        : reference loudness normalisation factor.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        audio_path = str(audio_path)
        logger.info("Encoding reference audio: %s", audio_path)
        t0 = time.perf_counter()

        self._encoded_prompt = self._model.encode_prompt(
            audio_path, duration=duration, rms=rms
        )
        self._ref_path = audio_path
        dt = time.perf_counter() - t0
        logger.info("Reference encoded in %.2f s", dt)

    def clear_reference(self) -> None:
        """Drop the currently loaded reference prompt."""
        self._encoded_prompt = None
        self._ref_path = None
        logger.info("Reference cleared.")

    # ── Text-to-speech ───────────────────────────────────────────
    def generate(
        self,
        text: str,
        *,
        num_steps: int = DEFAULT_NUM_STEPS,
        speed: float = DEFAULT_SPEED,
        t_shift: float = DEFAULT_T_SHIFT,
        return_smooth: bool = DEFAULT_RETURN_SMOOTH,
    ) -> np.ndarray:
        """Synthesise speech from *text* using the loaded reference.

        Returns
        -------
        numpy.ndarray — 1-D float32 waveform at 48 kHz.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded.")
        if self._encoded_prompt is None:
            raise RuntimeError("No reference audio set.")

        logger.info(
            "Generating speech  (steps=%d, speed=%.2f, t_shift=%.2f)",
            num_steps,
            speed,
            t_shift,
        )
        t0 = time.perf_counter()

        wav_tensor = self._model.generate_speech(
            text,
            self._encoded_prompt,
            num_steps=num_steps,
            t_shift=t_shift,
            speed=speed,
            return_smooth=return_smooth,
        )

        wav_np: np.ndarray = wav_tensor.numpy().squeeze()
        dt = time.perf_counter() - t0
        dur = len(wav_np) / SAMPLE_RATE
        rtf = dur / dt if dt > 0 else float("inf")
        logger.info(
            "Generated %.2f s of audio in %.2f s  (%.0f× realtime)", dur, dt, rtf
        )
        return wav_np

    # ── Convenience ──────────────────────────────────────────────
    def generate_and_save(
        self,
        text: str,
        output_path: str | Path,
        **kwargs,
    ) -> Path:
        """Generate speech and write to a 48 kHz WAV file."""
        import soundfile as sf  # lazy import

        wav = self.generate(text, **kwargs)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), wav, SAMPLE_RATE)
        logger.info("Saved → %s", output_path)
        return output_path
