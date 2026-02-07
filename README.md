# OptiClone — High-Speed Voice Cloning for Windows PC

A lightweight, zero-shot voice cloning desktop application powered by **LuxTTS** (150× realtime inference).

## Features

✅ **Zero-Shot Voice Cloning** — Clone any voice from a 3+ second reference audio sample  
✅ **High-Fidelity 48 kHz Output** — Crystal-clear, natural-sounding speech  
✅ **Blazing Fast** — Generates audio 150× faster than real-time on GPU  
✅ **Low VRAM Footprint** — Runs in <1 GB VRAM; ideal for multi-tasking  
✅ **Modern UI** — Dark-mode CustomTkinter interface with real-time controls  
✅ **CPU Friendly** — Works on CPU too (slower, but functional)  

## System Requirements

- **OS:** Windows 10+ (or Linux/macOS with Python 3.10+)
- **Python:** 3.10 or higher
- **GPU:** Optional (NVIDIA CUDA 11.8+ recommended; CPU works too!)
- **RAM:** 8 GB+ recommended
- **Disk:** ~5–10 GB for model weights (auto-downloaded on first run)

## Quick Start

### Option 1: One-Click Launcher (Windows Only)

1. Download or clone this repository
2. Double-click **`run.bat`**
3. Wait for dependencies to install (first run only, 5–10 min)
4. The OptiClone window will appear

### Option 2: Manual Setup (All Platforms)

```bash
# Create & activate venv
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run app
python main.py
```

## Usage

1. **Load a Reference** (3+ seconds of target voice)
   - Click **Upload WAV/MP3** to select a file, or  
   - Click **Record** to capture live microphone input

2. **Enter Text**
   - Type the script you want to clone in the text area

3. **Adjust Controls** (Optional)
   - **Inference Steps** (1–16): Higher = better quality, slower synthesis  
   - **Speed** (0.5–2.0×): Playback speed multiplier  
   - **Guidance Scale** (0.1–1.5): Higher = more adherence to reference voice

4. **Generate**
   - Click **Generate Voice**
   - Wait for synthesis to complete

5. **Play & Export**
   - Click **Play** to preview
   - Click **Export WAV** to save the output

## Tips for Best Results

- **Reference Audio:**
  - Minimum 3 seconds; 5–10 seconds optimal
  - Use clear, noise-free recordings
  - Match the target language/accent if possible

- **Inference Steps:**
  - Default (4) is fast & good quality
  - Use 8+ steps for studio-quality output
  - Use 1–2 for speed (sacrifices quality)

- **Guidance Scale:**
  - Default (0.9) balances quality & speaker similarity
  - Higher values (1.0+) favour the reference voice
  - Lower values (0.5–0.7) allow more variation

## Architecture

```
OptiClone/
├── run.bat                      # Windows one-click launcher
├── main.py                      # App entry point
├── requirements.txt             # Python dependencies
├── CLAUDE.md                    # Technical project notes
├── README.md                    # This file
└── opticlone/
    ├── __init__.py
    ├── config.py                # App constants & defaults
    ├── inference_engine.py      # LuxTTS model wrapper (core logic)
    ├── audio_utils.py           # Recording, playback, WAV I/O
    └── ui_main.py               # CustomTkinter GUI
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `inference_engine.py` | LuxTTS model loading, reference encoding, speech generation |
| `ui_main.py` | CustomTkinter GUI: controls, playback, file dialogs |
| `audio_utils.py` | Microphone recording, WAV export, playback threading |
| `config.py` | Constants: model paths, defaults, UI colors |

## Troubleshooting

### Issue: "Model not loaded" after startup

**Solution:** The first run downloads ~500 MB of model weights. Wait 2–5 minutes.  
Check the console (bottom of the window, if open) or `.opticlone.log` for details.

### Issue: CUDA out of memory (OOM)

**Solution:** 
1. Reduce **Inference Steps** to 1–2
2. Lower **Reference Duration** in code (`config.py`: `DEFAULT_REF_DURATION = 2`)
3. Use CPU instead by editing `inference_engine.py` to force `device='cpu'`

### Issue: No audio output / Playback fails

**Solution:**
1. Check system audio settings (Speaker enabled?)
2. Try exporting to WAV and playing with an external player
3. Verify `sounddevice` installed: `pip show sounddevice`

### Issue: Recording doesn't work

**Solution:**
1. Check mic permissions (Windows: Settings → Privacy → Microphone)
2. Test mic in system settings first
3. Use file upload instead of recording

### Issue: "Cannot import customtkinter" or other import errors

**Solution:**
```bash
pip install --upgrade setuptools wheel
pip install -r requirements.txt --force-reinstall
```

## Model Attribution

OptiClone uses models & code from:
- **LuxTTS** by [Yatharth Sharma](https://github.com/ysharma3501/LuxTTS)  
- **ZipVoice** by [K2-FSA Team](https://github.com/k2-fsa/ZipVoice)
- **Vocos Vocoder** by [Gemelo AI](https://github.com/gemelo-ai/vocos)

Licensed under **Apache 2.0** — see [LICENSE](LICENSE) in the repo.

## Citation

If you use OptiClone in research or production, please cite the original models:

```bibtex
@misc{sharma2025luxtts,
  title={LuxTTS: A High-Quality Rapid TTS Voice Cloning Model},
  author={Sharma, Yatharth and others},
  year={2025},
  howpublished={\url{https://github.com/ysharma3501/LuxTTS}}
}
```

## Disclaimer

This tool is for **personal, research, and authorized commercial use only**. Users are responsible for ensuring compliance with local laws regarding voice cloning and synthetic media. Unauthorized voice cloning of identifiable individuals may violate privacy and identity protection laws.

## Contributing

Found a bug or have a feature idea? Open an issue or pull request on GitHub!

## License

OptiClone is released under the **Apache 2.0 License** — same as LuxTTS.

---

**Made with ❤️ for voice enthusiasts and ML researchers.**
