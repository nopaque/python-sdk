"""Five-line Nopaque quickstart.

Before running: export NOPAQUE_API_KEY=your_key
"""
from nopaque import Nopaque

client = Nopaque()
print("Listing audio files in workspace:")
for audio in client.audio.list(limit=5):
    print(f"  {audio.id} - {audio.file_name}")
client.close()
