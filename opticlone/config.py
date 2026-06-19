"""App-wide constants and default configuration for OptiClone."""

# ── Model ────────────────────────────────────────────────────────
MODEL_REPO = "YatharthS/LuxTTS"
SAMPLE_RATE = 48_000  # Hz — native LuxTTS output rate

# ── Inference defaults ───────────────────────────────────────────
DEFAULT_NUM_STEPS = 4       # diffusion / sampling steps
DEFAULT_SPEED = 1.0         # playback speed multiplier
DEFAULT_T_SHIFT = 0.9       # guidance / sampling temperature
DEFAULT_RMS = 0.01          # reference loudness normalisation
DEFAULT_REF_DURATION = 5    # seconds of reference audio to encode
DEFAULT_RETURN_SMOOTH = False

# ── Slider ranges ────────────────────────────────────────────────
STEPS_MIN, STEPS_MAX = 1, 16
SPEED_MIN, SPEED_MAX = 0.5, 2.0
GUIDANCE_MIN, GUIDANCE_MAX = 0.1, 1.5   # maps to t_shift

# ── UI ───────────────────────────────────────────────────────────
APP_TITLE = "OptiClone — Voice Cloner"
WINDOW_SIZE = "1000x780"
# Modern gradient-inspired color palette
DARK_BG = "#0f0f23"          # Deep dark blue-black
CARD_BG = "#1a1d3a"          # Card background
ACCENT = "#2d3561"           # Accent frame color
ACCENT_LIGHT = "#3d4575"     # Lighter accent
HIGHLIGHT = "#6366f1"        # Indigo primary
HIGHLIGHT_HOVER = "#818cf8"  # Lighter indigo for hover
SUCCESS = "#10b981"          # Green for success
WARNING = "#f59e0b"          # Amber for warnings
ERROR = "#ef4444"            # Red for errors
TEXT_PRIMARY = "#f8fafc"     # Near white
TEXT_SECONDARY = "#94a3b8"   # Muted gray
BORDER_COLOR = "#374151"     # Subtle border

# ── Recording ────────────────────────────────────────────────────
REC_CHANNELS = 1
REC_SAMPLE_RATE = 48_000
REC_DTYPE = "float32"
