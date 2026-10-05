import sys
import threading
from pathlib import Path

_sound_lock = threading.Lock()


def play_sound_async(sound_path: Path | str) -> None:
    """Plays an audio file asynchronously in a background thread."""
    path = Path(sound_path)
    if not path.exists():
        print(f"[Audio] ❌ File not found: {path}")
        return

    def _worker():
        with _sound_lock:
            if sys.platform == "win32":
                import winsound
                try:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                except Exception as e:
                    print(f"[Audio] ❌ Playback error: {e}")
            else:
                print(f"[Audio] 🔊 Simulated playback: {path.name}")

    threading.Thread(target=_worker, daemon=True).start()