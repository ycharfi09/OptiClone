"""
audio_utils.py — Recording, playback, and WAV-file helpers for OptiClone.
"""

from __future__ import annotations

import io
import logging
import threading
import wave
from pathlib import Path
from typing import Optional

import numpy as np

from opticlone.config import REC_CHANNELS, REC_DTYPE, REC_SAMPLE_RATE, SAMPLE_RATE

logger = logging.getLogger("opticlone.audio")


# ── WAV export ───────────────────────────────────────────────────
def save_wav(wav: np.ndarray, path: str | Path, sr: int = SAMPLE_RATE) -> Path:
    """Write a float32 numpy array to a 48 kHz WAV file."""
    import soundfile as sf

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), wav, sr)
    logger.info("WAV saved → %s", path)
    return path


def wav_to_bytes(wav: np.ndarray, sr: int = SAMPLE_RATE) -> bytes:
    """Convert a float32 waveform to in-memory WAV bytes (for playback)."""
    buf = io.BytesIO()
    # Scale float32 → int16 for broad compatibility
    pcm = np.clip(wav, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


# ── Playback (sounddevice) ───────────────────────────────────────
class AudioPlayer:
    """Simple non-blocking audio player backed by sounddevice."""

    def __init__(self) -> None:
        self._stream = None
        self._playing = False

    @property
    def is_playing(self) -> bool:
        return self._playing

    def play(self, wav: np.ndarray, sr: int = SAMPLE_RATE) -> None:
        """Play *wav* through the default output device."""
        import sounddevice as sd

        self.stop()
        self._playing = True

        def _finished_cb():
            self._playing = False

        def _run():
            try:
                sd.play(wav, samplerate=sr)
                sd.wait()
            except Exception as exc:
                logger.error("Playback error: %s", exc)
            finally:
                _finished_cb()

        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        import sounddevice as sd

        sd.stop()
        self._playing = False


# ── Recording (sounddevice) ──────────────────────────────────────
class AudioRecorder:
    """Microphone recorder that captures audio in a background thread."""

    def __init__(self) -> None:
        self._recording = False
        self._frames: list[np.ndarray] = []
        self._thread: Optional[threading.Thread] = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        """Begin recording from the default input device."""
        import sounddevice as sd

        if self._recording:
            return
        self._frames.clear()
        self._recording = True

        def _capture():
            try:
                with sd.InputStream(
                    samplerate=REC_SAMPLE_RATE,
                    channels=REC_CHANNELS,
                    dtype=REC_DTYPE,
                    blocksize=4096,
                ) as stream:
                    while self._recording:
                        data, _ = stream.read(4096)
                        self._frames.append(data.copy())
            except Exception as exc:
                logger.error("Recording error: %s", exc)
            finally:
                self._recording = False

        self._thread = threading.Thread(target=_capture, daemon=True)
        self._thread.start()
        logger.info("Recording started.")

    def stop(self) -> Optional[np.ndarray]:
        """Stop recording and return the captured waveform (float32, 48 kHz)."""
        if not self._recording:
            return None
        self._recording = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if not self._frames:
            return None
        wav = np.concatenate(self._frames, axis=0).squeeze()
        logger.info("Recorded %.2f s of audio.", len(wav) / REC_SAMPLE_RATE)
        return wav

    def save(self, path: str | Path) -> Optional[Path]:
        """Stop recording and persist to disk."""
        wav = self.stop()
        if wav is None:
            return None
        return save_wav(wav, path, sr=REC_SAMPLE_RATE)


# ── Validation ───────────────────────────────────────────────────
def validate_reference(path: str | Path) -> tuple[bool, str]:
    """Check that a reference file is usable (exists, ≥ 3 s, audio format)."""
    import soundfile as sf

    path = Path(path)
    if not path.exists():
        return False, f"File not found: {path}"
    if path.suffix.lower() not in {".wav", ".mp3", ".flac", ".ogg"}:
        return False, f"Unsupported format: {path.suffix}"
    try:
        info = sf.info(str(path))
        duration = info.duration
        if duration < 2.0:
            return False, f"Audio too short ({duration:.1f} s). Use ≥ 3 s."
        return True, f"OK — {duration:.1f} s, {info.samplerate} Hz"
    except Exception as exc:
        return False, f"Cannot read file: {exc}"
