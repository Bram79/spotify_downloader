#!/usr/bin/env python3
"""Lokale web-interface voor de Spotify-downloader. Draait alleen op 127.0.0.1."""
import io
import re
import subprocess
import threading
import uuid
import zipfile
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file

BASE = Path(__file__).parent
SPOTDL = BASE / ".venv" / "bin" / "spotdl"
OUT = BASE / "downloads"
URL_RE = re.compile(r"^https?://open\.spotify\.com/(?:intl-[a-z]+/)?(track|album|playlist)/\w+")
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

app = Flask(__name__)
jobs: dict[str, dict] = {}


def run_job(job_id: str, url: str, bitrate: str) -> None:
    job = jobs[job_id]
    job_dir = OUT / job_id
    template = str(job_dir / "{album-artist} - {album}" / "{track-number} - {title}.{output-ext}")
    proc = subprocess.Popen(
        [str(SPOTDL), "download", url, "--audio", "youtube-music", "soundcloud", "--format", "mp3", "--bitrate", bitrate,
         "--ffmpeg-args", "-af silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.2", "--output", template],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    for line in proc.stdout:
        line = ANSI.sub("", line).strip()
        if not line:
            continue
        if "Error" in line:
            job["errors"] += 1
        if line.startswith("Downloaded"):
            job["done_tracks"] += 1
        m = re.search(r"Found (\d+) songs", line)
        if m:
            job["total"] = int(m.group(1))
    ok = proc.wait() == 0 and job["errors"] == 0
    files = sorted(job_dir.rglob("*.mp3"))
    if files:
        job["name"] = files[0].parent.name if len(files) > 1 else files[0].stem
    job["files"] = len(files)
    job["status"] = "klaar" if ok else "fout"


@app.post("/api/download")
def start():
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    bitrate = data.get("bitrate", "320k")
    if not URL_RE.match(url):
        return jsonify(error="Dit is geen geldige Spotify-link (track, album of playlist)."), 400
    if bitrate not in ("128k", "192k", "256k", "320k"):
        bitrate = "320k"
    job_id = uuid.uuid4().hex[:8]
    jobs[job_id] = {"url": url, "status": "bezig", "name": "", "files": 0, "done_tracks": 0, "total": 1, "errors": 0}
    threading.Thread(target=run_job, args=(job_id, url, bitrate), daemon=True).start()
    return jsonify(id=job_id)


@app.get("/api/jobs")
def list_jobs():
    return jsonify([{"id": k, **v} for k, v in reversed(jobs.items())])


@app.get("/api/file/<job_id>")
def get_file(job_id):
    if job_id not in jobs or not re.fullmatch(r"[0-9a-f]{8}", job_id):
        abort(404)
    files = sorted((OUT / job_id).rglob("*.mp3"))
    if not files:
        abort(404)
    if len(files) == 1:
        return send_file(files[0], as_attachment=True, download_name=files[0].name)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for f in files:
            z.write(f, f.name)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{jobs[job_id]['name'] or 'muziek'}.zip")


@app.get("/")
def index():
    return PAGE


PAGE = """<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Muziek Downloader</title>
<style>
:root{--bg:#0f1115;--card:#181b22;--line:#262a34;--text:#eef0f4;--mute:#8a90a0;--accent:#1db954;--err:#ff5d5d}
@media (prefers-color-scheme:light){:root{--bg:#f4f5f8;--card:#fff;--line:#e2e5ec;--text:#14161b;--mute:#6a7080}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:680px;margin:0 auto;padding:48px 16px}
h1{font-size:28px;margin:0 0 4px}
p.sub{color:var(--mute);margin:0 0 28px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px}
form{display:flex;flex-wrap:wrap;gap:10px}
input,select,button{font:inherit;border-radius:10px;border:1px solid var(--line);padding:12px 14px;background:var(--bg);color:var(--text)}
input{flex:1 1 100%}
select{flex:1}
button{flex:2;background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600;cursor:pointer}
button:disabled{opacity:.6;cursor:default}
#err{color:var(--err);margin:10px 0 0;min-height:1.5em;font-size:14px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:32px 0 12px}
.job{margin-bottom:12px}
.job .url{font-size:14px;color:var(--mute);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin:10px 0 8px}
.bar div{height:100%;background:var(--accent);transition:width .4s}
.job.fout .bar div{background:var(--err)}
.meta{display:flex;justify-content:space-between;font-size:14px}
.dl{display:inline-block;margin-top:12px;padding:10px 16px;border-radius:10px;background:var(--accent);color:#fff;font-weight:600;text-decoration:none}
.empty{color:var(--mute);text-align:center;padding:12px}
</style></head><body><main>
<h1>Muziek Downloader</h1>
<p class="sub">Plak een Spotify-link van een nummer, album of playlist. Alleen voor persoonlijk gebruik.</p>
<div class="card"><form id="f">
<input id="url" placeholder="https://open.spotify.com/album/..." autocomplete="off" required>
<select id="br"><option>320k</option><option>256k</option><option>192k</option><option>128k</option></select>
<button id="go">Downloaden</button>
</form><div id="err"></div></div>
<h2>Downloads</h2><div id="jobs"><div class="card empty">Nog niets gedownload.</div></div>
<script>
const $=id=>document.getElementById(id), esc=s=>s.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
$("f").onsubmit=async e=>{
  e.preventDefault();$("err").textContent="";$("go").disabled=true;
  const r=await fetch("/api/download",{method:"POST",body:JSON.stringify({url:$("url").value,bitrate:$("br").value})});
  const d=await r.json();$("go").disabled=false;
  if(!r.ok){$("err").textContent=d.error;return}
  $("url").value="";refresh();
};
async function refresh(){
  const jobs=await (await fetch("/api/jobs")).json();
  if(!jobs.length)return;
  $("jobs").innerHTML=jobs.map(j=>{
    const pct=j.status==="klaar"?100:Math.min(99,Math.round(j.done_tracks/j.total*100));
    const label=j.status==="bezig"?`${j.done_tracks} / ${j.total} nummers`:j.status==="klaar"?`Klaar (${j.done_tracks} nummers)`:`Niet alles gelukt (${j.errors} fout${j.errors===1?"":"en"})`;
    return `<div class="card job ${j.status}"><div class="url">${esc(j.name||j.url)}</div>
    <div class="bar"><div style="width:${pct}%"></div></div>
    <div class="meta"><span>${label}</span><span>${pct}%</span></div>
    ${j.files?`<a class="dl" href="/api/file/${j.id}">${j.files>1?"Download zip":"Download mp3"}</a>`:""}</div>`}).join("");
}
setInterval(refresh,1000);refresh();
</script></main></body></html>"""

if __name__ == "__main__":
    print("Open http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001)
