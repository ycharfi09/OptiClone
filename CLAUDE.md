# OptiClone — Project Tracking

## Overview
OptiClone is a standalone Windows PC voice cloning application built with Python.
It integrates the **LuxTTS** model (by YatharthS, based on ZipVoice) for high-speed
(150× realtime) zero-shot voice cloning at 48 kHz fidelity.

## Architecture

```
OptiClone/
├── CLAUDE.md              # This file — project tracking
├── README.md              # User-facing documentation
├── requirements.txt       # Python dependencies
├── run.bat                # One-click Windows launcher
├── main.py                # Entry point
├── opticlone/
│   ├── __init__.py
│   ├── inference_engine.py   # LuxTTS model wrapper
│   ├── ui_main.py            # CustomTkinter GUI
│   ├── audio_utils.py        # Recording / WAV helpers
│   └── config.py             # App-wide constants & defaults
└── assets/
    └── icon.png              # App icon placeholder
```

## Key Decisions
| Decision | Choice | Rationale |
|---|---|---|
| Model source | HuggingFace `YatharthS/LuxTTS` | Official weights; auto-downloaded on first run |
| UI framework | CustomTkinter | Modern dark-mode look; pure Python; lightweight |
| Backend | Direct in-process calls | No FastAPI needed for a local desktop app |
| Audio I/O | soundfile + sounddevice | Cross-platform recording & WAV export |
| Sample rate | 48 000 Hz | Native LuxTTS output rate |

## LuxTTS API Reference (from upstream repo)
```python
from zipvoice.luxvoice import LuxTTS

lux_tts = LuxTTS('YatharthS/LuxTTS', device='cuda')       # or 'cpu'
encoded  = lux_tts.encode_prompt('ref.wav', duration=5, rms=0.01)
wav      = lux_tts.generate_speech(text, encoded,
              num_steps=4, t_shift=0.9, speed=1.0,
              return_smooth=False)
```

## Build / Run Commands
```bash
# Create venv & install
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run the app
python main.py
```

## Status
- [x] Project scaffolded
- [x] CLAUDE.md created
- [x] requirements.txt drafted
- [x] inference_engine.py implemented
- [x] ui_main.py implemented
- [x] main.py entry point created
- [x] audio_utils.py helper module
- [x] config.py constants
- [x] README.md written
- [x] run.bat launcher
