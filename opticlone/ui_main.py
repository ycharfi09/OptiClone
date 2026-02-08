"""
ui_main.py — CustomTkinter GUI for OptiClone voice cloning.

Modern dark-mode interface with real-time controls, audio preview, and file export.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image

from opticlone.audio_utils import AudioPlayer, AudioRecorder, validate_reference
from opticlone.config import (
    ACCENT,
    ACCENT_LIGHT,
    APP_TITLE,
    BORDER_COLOR,
    CARD_BG,
    DARK_BG,
    DEFAULT_NUM_STEPS,
    DEFAULT_SPEED,
    DEFAULT_T_SHIFT,
    ERROR,
    GUIDANCE_MAX,
    GUIDANCE_MIN,
    HIGHLIGHT,
    HIGHLIGHT_HOVER,
    SAMPLE_RATE,
    SPEED_MAX,
    SPEED_MIN,
    STEPS_MAX,
    STEPS_MIN,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
    WINDOW_SIZE,
)
from opticlone.inference_engine import InferenceEngine

logger = logging.getLogger("opticlone.ui")

# Configure app appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class OptiCloneApp(ctk.CTk):
    """Main application window for OptiClone."""

    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.resizable(True, True)
        self.configure(fg_color=DARK_BG)

        # ── State ────────────────────────────────────────────────
        self.engine = InferenceEngine()
        self.player = AudioPlayer()
        self.recorder = AudioRecorder()
        self._last_generated_wav: Optional[bytes] = None
        self._generating = False
        self._loading_model = False

        # ── Layout grid ──────────────────────────────────────────
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)  # Text area grows

        # ── Title with gradient effect ──────────────────────────
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="ew")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🎙️ OptiClone",
            font=("Segoe UI", 28, "bold"),
            text_color=HIGHLIGHT,
        )
        title_label.pack(side="left")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="High-Speed Voice Cloning with LuxTTS",
            font=("Segoe UI", 12),
            text_color=TEXT_SECONDARY,
        )
        subtitle_label.pack(side="left", padx=(10, 0), pady=(8, 0))

        # ── Reference audio section (card style) ────────────────
        ref_frame = ctk.CTkFrame(
            main_frame, 
            fg_color=CARD_BG, 
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR
        )
        ref_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        ref_frame.grid_columnconfigure(1, weight=1)

        ref_label = ctk.CTkLabel(
            ref_frame, 
            text="📁 Reference Audio", 
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIMARY
        )
        ref_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.ref_status_label = ctk.CTkLabel(
            ref_frame,
            text="No reference loaded",
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY,
        )
        self.ref_status_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        self.btn_upload = ctk.CTkButton(
            ref_frame,
            text="📂 Upload File",
            command=self._upload_reference,
            fg_color=ACCENT,
            hover_color=ACCENT_LIGHT,
            corner_radius=8,
            height=36,
            width=130,
            state="disabled",
            font=("Segoe UI", 11, "bold")
        )
        self.btn_upload.grid(row=0, column=2, padx=8, pady=15)

        self.btn_record = ctk.CTkButton(
            ref_frame,
            text="🎤 Record",
            command=self._toggle_recording,
            fg_color=ACCENT,
            hover_color=ACCENT_LIGHT,
            corner_radius=8,
            height=36,
            width=110,
            state="disabled",
            font=("Segoe UI", 11, "bold")
        )
        self.btn_record.grid(row=0, column=3, padx=(0, 20), pady=15)

        # ── Inference controls (card style) ──────────────────────
        ctrl_frame = ctk.CTkFrame(
            main_frame, 
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR
        )
        ctrl_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        ctrl_frame.grid_columnconfigure(1, weight=1)

        # Card title
        ctk.CTkLabel(
            ctrl_frame, 
            text="⚙️ Generation Settings", 
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIMARY
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 10), sticky="w")

        # Inference steps
        ctk.CTkLabel(
            ctrl_frame, 
            text="Inference Steps:", 
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY
        ).grid(row=1, column=0, padx=(20, 10), pady=10, sticky="e")
        
        self.steps_var = ctk.IntVar(value=DEFAULT_NUM_STEPS)
        self.steps_slider = ctk.CTkSlider(
            ctrl_frame,
            from_=STEPS_MIN,
            to=STEPS_MAX,
            number_of_steps=STEPS_MAX - STEPS_MIN,
            variable=self.steps_var,
            button_color=HIGHLIGHT,
            button_hover_color=HIGHLIGHT_HOVER,
            progress_color=HIGHLIGHT,
            height=18,
        )
        self.steps_slider.grid(row=1, column=1, padx=15, pady=10, sticky="ew")
        self.steps_label = ctk.CTkLabel(
            ctrl_frame, 
            text=str(DEFAULT_NUM_STEPS), 
            font=("Segoe UI", 11, "bold"),
            text_color=HIGHLIGHT,
            width=50
        )
        self.steps_label.grid(row=1, column=2, padx=(5, 20), pady=10)
        self.steps_var.trace("w", lambda *_: self.steps_label.configure(
            text=str(self.steps_var.get())
        ))

        # Speed
        ctk.CTkLabel(
            ctrl_frame, 
            text="Speed:", 
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY
        ).grid(row=2, column=0, padx=(20, 10), pady=10, sticky="e")
        
        self.speed_var = ctk.DoubleVar(value=DEFAULT_SPEED)
        self.speed_slider = ctk.CTkSlider(
            ctrl_frame,
            from_=SPEED_MIN,
            to=SPEED_MAX,
            variable=self.speed_var,
            button_color=HIGHLIGHT,
            button_hover_color=HIGHLIGHT_HOVER,
            progress_color=HIGHLIGHT,
            height=18,
        )
        self.speed_slider.grid(row=2, column=1, padx=15, pady=10, sticky="ew")
        self.speed_label = ctk.CTkLabel(
            ctrl_frame, 
            text=f"{DEFAULT_SPEED:.2f}x", 
            font=("Segoe UI", 11, "bold"),
            text_color=HIGHLIGHT,
            width=50
        )
        self.speed_label.grid(row=2, column=2, padx=(5, 20), pady=10)
        self.speed_var.trace("w", lambda *_: self.speed_label.configure(
            text=f"{self.speed_var.get():.2f}x"
        ))

        # Guidance Scale (maps to t_shift)
        ctk.CTkLabel(
            ctrl_frame, 
            text="Guidance Scale:", 
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY
        ).grid(row=3, column=0, padx=(20, 10), pady=(10, 15), sticky="e")
        
        self.guidance_var = ctk.DoubleVar(value=DEFAULT_T_SHIFT)
        self.guidance_slider = ctk.CTkSlider(
            ctrl_frame,
            from_=GUIDANCE_MIN,
            to=GUIDANCE_MAX,
            variable=self.guidance_var,
            button_color=HIGHLIGHT,
            button_hover_color=HIGHLIGHT_HOVER,
            progress_color=HIGHLIGHT,
            height=18,
        )
        self.guidance_slider.grid(row=3, column=1, padx=15, pady=(10, 15), sticky="ew")
        self.guidance_label = ctk.CTkLabel(
            ctrl_frame,
            text=f"{DEFAULT_T_SHIFT:.2f}",
            font=("Segoe UI", 11, "bold"),
            text_color=HIGHLIGHT,
            width=50,
        )
        self.guidance_label.grid(row=3, column=2, padx=(5, 20), pady=(10, 15))
        self.guidance_var.trace("w", lambda *_: self.guidance_label.configure(
            text=f"{self.guidance_var.get():.2f}"
        ))

        # ── Script input (card style) ────────────────────────────
        script_frame = ctk.CTkFrame(
            main_frame,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR
        )
        script_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        script_frame.grid_columnconfigure(0, weight=1)
        script_frame.grid_rowconfigure(1, weight=1)
        
        script_label = ctk.CTkLabel(
            script_frame, 
            text="📝 Script to Synthesize", 
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIMARY
        )
        script_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")

        self.script_textbox = ctk.CTkTextbox(
            script_frame, 
            height=100, 
            fg_color=ACCENT,
            border_width=0,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 11),
            corner_radius=8
        )
        self.script_textbox.grid(
            row=1, column=0, padx=20, pady=(0, 15), sticky="ew"
        )
        self.script_textbox.insert("0.0", "Hey, what's up? I'm feeling great!")

        # ── Generate button (prominent) ──────────────────────────
        self.generate_btn = ctk.CTkButton(
            main_frame,
            text="✨ Generate Voice",
            command=self._generate,
            font=("Segoe UI", 15, "bold"),
            fg_color=HIGHLIGHT,
            hover_color=HIGHLIGHT_HOVER,
            height=56,
            corner_radius=12,
            border_width=2,
            border_color=HIGHLIGHT_HOVER,
        )
        self.generate_btn.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 20))

        # ── Playback controls (card style) ───────────────────────
        play_frame = ctk.CTkFrame(
            main_frame,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR
        )
        play_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        play_frame.grid_columnconfigure(1, weight=1)

        self.play_btn = ctk.CTkButton(
            play_frame,
            text="▶️ Play",
            command=self._play,
            fg_color=SUCCESS,
            hover_color="#059669",
            corner_radius=8,
            height=40,
            width=110,
            state="disabled",
            font=("Segoe UI", 11, "bold")
        )
        self.play_btn.grid(row=0, column=0, padx=20, pady=15)

        self.status_label = ctk.CTkLabel(
            play_frame,
            text="◯ Ready",
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY,
        )
        self.status_label.grid(row=0, column=1, padx=15, pady=15, sticky="w")

        self.export_btn = ctk.CTkButton(
            play_frame,
            text="💾 Export WAV",
            command=self._export,
            fg_color=ACCENT,
            hover_color=ACCENT_LIGHT,
            corner_radius=8,
            height=40,
            width=130,
            state="disabled",
            font=("Segoe UI", 11, "bold")
        )
        self.export_btn.grid(row=0, column=2, padx=(5, 20), pady=15)

        # ── Status bar ───────────────────────────────────────────
        self.info_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Segoe UI", 10),
            text_color=TEXT_SECONDARY,
        )
        self.info_label.grid(row=7, column=0, columnspan=3, sticky="w", pady=(5, 0))

        # ── Init model in background ─────────────────────────────
        threading.Thread(target=self._init_engine, daemon=True).start()

    # ── Engine lifecycle ─────────────────────────────────────────
    def _init_engine(self) -> None:
        """Load the LuxTTS model in the background."""
        try:
            self._loading_model = True
            self._update_status("⏳ Loading LuxTTS model…")
            self.engine.load_model()
            self._update_status("✓ Model ready", color=SUCCESS)
            # Enable reference buttons once model is loaded
            self.after(0, lambda: self.btn_upload.configure(state="normal"))
            self.after(0, lambda: self.btn_record.configure(state="normal"))
        except Exception as exc:
            logger.exception("Failed to load model")
            self._update_status(f"✗ Error: {exc}", color=ERROR)
        finally:
            self._loading_model = False

    # ── Reference upload ─────────────────────────────────────────
    def _upload_reference(self) -> None:
        """Open file dialog to select a reference audio."""
        if not self.engine.is_loaded:
            messagebox.showerror("Model", "Model not ready yet. Please wait.")
            return

        path = filedialog.askopenfilename(
            title="Select Reference Audio",
            filetypes=[("Audio Files", "*.wav *.mp3 *.flac"), ("All", "*.*")],
        )
        if not path:
            return

        ok, msg = validate_reference(path)
        if not ok:
            messagebox.showerror("Invalid Audio", msg)
            return

        try:
            self._update_status(f"⏳ Encoding {Path(path).name}…")
            self.engine.set_reference(path)
            self.ref_status_label.configure(
                text=str(Path(path).name), text_color=SUCCESS
            )
            self._update_status(f"✓ Reference loaded: {Path(path).name}")
        except Exception as exc:
            logger.exception("Failed to set reference")
            messagebox.showerror("Error", f"Failed to encode reference: {exc}")
            self._update_status("✗ Reference failed", color=ERROR)

    def _toggle_recording(self) -> None:
        """Start/stop microphone recording."""
        if not self.recorder.is_recording and not self.engine.is_loaded:
            messagebox.showerror("Model", "Model not ready yet. Please wait.")
            return

        if self.recorder.is_recording:
            wav = self.recorder.stop()
            if wav is not None:
                # Save temp file and set it as reference
                temp_path = Path.home() / ".opticlone" / "temp_recording.wav"
                from opticlone.audio_utils import save_wav
                save_wav(wav, temp_path)
                self._update_status("✓ Recording saved. Setting as reference…")
                try:
                    self.engine.set_reference(str(temp_path))
                    self.ref_status_label.configure(
                        text="🎤 Recorded (live)", text_color=SUCCESS
                    )
                    self._update_status("✓ Live recording set as reference")
                except Exception as exc:
                    logger.exception("Failed to set recorded reference")
                    messagebox.showerror("Error", f"Failed to use recording: {exc}")
        else:
            self.recorder.start()
            self.ref_status_label.configure(text="🎤 Recording…", text_color=WARNING)
            self._update_status("🎤 Recording started")

    # ── Text generation ──────────────────────────────────────────
    def _generate(self) -> None:
        """Generate speech from the script."""
        if self._generating or self._loading_model:
            messagebox.showwarning(
                "Busy", "Generation or model loading in progress…"
            )
            return

        if not self.engine.is_loaded:
            messagebox.showerror("Model", "Model not ready yet. Please wait.")
            return

        if not self.engine.has_reference:
            messagebox.showerror("Reference", "No reference audio loaded.")
            return

        text = self.script_textbox.get("0.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Text", "Please enter some text to generate.")
            return

        self._generating = True
        self.generate_btn.configure(state="disabled")
        self._update_status("⏳ Generating…")

        def _run():
            try:
                wav = self.engine.generate(
                    text,
                    num_steps=self.steps_var.get(),
                    speed=self.speed_var.get(),
                    t_shift=self.guidance_var.get(),
                )
                # Store as WAV bytes for playback/export
                from opticlone.audio_utils import wav_to_bytes
                self._last_generated_wav = wav_to_bytes(wav, sr=SAMPLE_RATE)
                dur_sec = len(wav) / SAMPLE_RATE
                self._update_status(
                    f"✓ Generated {dur_sec:.1f}s",
                    color=SUCCESS,
                )
                self.play_btn.configure(state="normal")
                self.export_btn.configure(state="normal")
            except Exception as exc:
                logger.exception("Generation failed")
                self._update_status(f"✗ Error: {exc}", color=ERROR)
                messagebox.showerror("Generation", f"Failed: {exc}")
            finally:
                self._generating = False
                self.generate_btn.configure(state="normal")

        threading.Thread(target=_run, daemon=True).start()

    def _play(self) -> None:
        """Play the last generated audio."""
        if self._last_generated_wav is None:
            messagebox.showwarning("Audio", "No generated audio to play.")
            return
        import io
        import wave
        import numpy as np

        # Convert WAV bytes back to numpy for playback
        buf = io.BytesIO(self._last_generated_wav)
        with wave.open(buf, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            pcm = np.frombuffer(frames, dtype=np.int16)
            wav = pcm.astype(np.float32) / 32767.0

        self._update_status("▶️ Playing…")
        self.player.play(wav, sr=SAMPLE_RATE)

        def _done():
            if not self.player.is_playing:
                self._update_status("✓ Playback done")

        threading.Thread(target=_done, daemon=True).start()

    def _export(self) -> None:
        """Save the generated audio to disk."""
        if self._last_generated_wav is None:
            messagebox.showwarning("Audio", "No generated audio to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV", "*.wav"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            import io
            import wave
            import numpy as np
            from pathlib import Path

            # Write WAV to disk
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            buf = io.BytesIO(self._last_generated_wav)
            with wave.open(buf, "rb") as src:
                with wave.open(str(output_path), "wb") as dst:
                    dst.setnchannels(src.getnchannels())
                    dst.setsampwidth(src.getsampwidth())
                    dst.setframerate(src.getframerate())
                    dst.writeframes(src.readframes(src.getnframes()))

            self._update_status(f"✓ Exported → {output_path.name}")
            messagebox.showinfo("Success", f"Saved:\n{output_path}")
        except Exception as exc:
            logger.exception("Export failed")
            messagebox.showerror("Export", f"Failed: {exc}")

    # ── Helpers ──────────────────────────────────────────────────
    def _update_status(self, msg: str, color: str = None) -> None:
        """Update the info label."""
        if color is None:
            color = TEXT_SECONDARY
        self.after(0, lambda: self.info_label.configure(text=msg, text_color=color))

    def on_closing(self) -> None:
        """Cleanup on window close."""
        try:
            self.recorder.stop()
            self.player.stop()
            self.engine.unload_model()
        except Exception as exc:
            logger.warning("Cleanup error: %s", exc)
        self.destroy()


def run_app() -> None:
    """Launch the OptiClone GUI."""
    app = OptiCloneApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
