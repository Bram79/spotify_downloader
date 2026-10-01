# Spotify Downloader

Lokale tool om Spotify-links (nummer, album of playlist) als mp3 te downloaden, met een eenvoudige web-interface.

Spotify zelf is DRM-beveiligd. De tool leest de metadata uit de Spotify-link (via [spotdl](https://github.com/spotDL/spotify-downloader)), zoekt het nummer op YouTube Music (met YouTube, SoundCloud en Piped als reserve; mislukte nummers worden tot 3 keer opnieuw geprobeerd) en zet het om naar mp3 met titel, artiest, album en hoes.

> Alleen voor persoonlijk gebruik. Zet dit niet openbaar online: dat is juridisch riskant.

## Installeren

### Windows

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt deno
venv\Scripts\spotdl --download-ffmpeg
```

Starten: dubbelklik `start.bat`, of `venv\Scripts\python app.py`.

### macOS

Vereist Python 3 en Homebrew.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
brew install ffmpeg deno
```

## Gebruik

### Web-interface

```bash
.venv/bin/python app.py
```

Open http://127.0.0.1:5001, plak een Spotify-link en klik op Downloaden. Een nummer komt als `.mp3`, een album of playlist als `.zip`. De server luistert alleen op `127.0.0.1`.

### Commandoregel

```bash
.venv/bin/python download.py <spotify-link> [-o map] [-b 320k]
```

Bestanden komen standaard in `downloads/`.

## Goed om te weten

- **Kwaliteit:** de bron (YouTube Music, YouTube of SoundCloud) bepaalt de kwaliteit, niet de bitrate. Meer dan de bron heeft, kan mp3 320k niet geven.
- **Stilte aan het begin** wordt automatisch weggeknipt, want sommige bronnen beginnen met een lange stille intro.
- **Verkeerde versie:** bij obscure nummers kan de match afwijken (live, remix). Controleer dat even.
- **Poort:** 5001 in plaats van 5000, omdat macOS 5000 gebruikt voor AirPlay.
- **iPod:** importeer de mp3's in de Muziek-app en synchroniseer via Finder.
