#!/usr/bin/env python3
"""Download Spotify-tracks, -albums of -playlists als mp3 (via spotdl)."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

SPOTIFY_URL = re.compile(r"^https?://open\.spotify\.com/(?:intl-[a-z]+/)?(track|album|playlist)/\w+")
SPOTDL = Path(__file__).parent / ".venv" / "bin" / "spotdl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="Spotify-links (track, album of playlist)")
    parser.add_argument("-o", "--output", default="downloads", help="doelmap (standaard: downloads)")
    parser.add_argument("-b", "--bitrate", default="320k", help="mp3-bitrate (standaard: 320k)")
    args = parser.parse_args()

    for url in args.urls:
        if not SPOTIFY_URL.match(url):
            print(f"Geen geldige Spotify-link: {url}", file=sys.stderr)
            return 1

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    # Albums en playlists komen in een eigen map: Artiest/Album/nummer
    template = str(out / "{album-artist}" / "{album}" / "{track-number} - {title}.{output-ext}")

    cmd = [str(SPOTDL), "download", *args.urls,
           "--format", "mp3", "--bitrate", args.bitrate, "--output", template]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
