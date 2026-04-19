"""Upload a local audio file, then download it by ID."""
import sys
from pathlib import Path

from nopaque import Nopaque

if len(sys.argv) != 2:
    print("Usage: python audio_upload.py <path-to-audio-file>")
    sys.exit(1)

path = Path(sys.argv[1])
with Nopaque() as client:
    audio = client.audio.upload(file=str(path))
    print(f"Uploaded {audio.id} ({audio.file_name})")

    out = Path("downloaded.wav")
    client.audio.download(audio.id, to=str(out))
    print(f"Downloaded to {out}")
