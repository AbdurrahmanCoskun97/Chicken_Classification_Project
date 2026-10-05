from pathlib import Path
import sys


def get_resource_path(relative_path: str) -> Path:
    """Resolves absolute path for both development and bundled executables."""
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path


# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"

DEFAULT_INPUT_FOLDER = DEFAULT_DATA_DIR / "received_images"
DEFAULT_OUTPUT_FOLDER = DEFAULT_DATA_DIR / "output"
DEFAULT_WRONG_FOLDER = DEFAULT_DATA_DIR / "wrong_classifications"

SOUND_FOLDER = get_resource_path("Sounds")
LOGO_FOLDER = get_resource_path("Logo")

# Network Configuration
IMAGE_PORT = 5001
SEND_BACK_PORT = 6000
DEFAULT_RASPBERRY_IP = "0.0.0.0"

# Model Configuration
CLASS_NAMES = ['Breasts', 'ButterfliedDrumsticks', 'Drumsticks', 'WholeLeg', 'Wings']

SOUND_MAP = {
    "Drumsticks": "Drumsticks.wav",
    "WholeLeg": "WholeLeg.wav",
    "Wings": "Wings.wav",
    "Breasts": "Breast.wav",
    "ButterfliedDrumsticks": "ButterfliedDrumsticks.wav"
}