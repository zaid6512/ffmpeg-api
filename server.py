# D:\ffmpeg-api\server.py
from flask import Flask, request, send_file, jsonify
import subprocess, tempfile, requests, os

app = Flask(__name__)

@app.route('/trim', methods=['POST'])
def trim():
    data = request.get_json(force=True)
    url = data.get('video_url')
    start = data.get('start')
    duration = data.get('duration') or (data.get('end') and (float(data.get('end')) - float(start)))
    if not url or start is None or duration is None:
        return jsonify({"error":"video_url, start, and duration (or end) required"}), 400

    # create temp files
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_in.close()
    tmp_out.close()

    # download file (stream)
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    with open(tmp_in.name, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)

    # run ffmpeg trim (fast copy)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", tmp_in.name,
        "-c", "copy",
        tmp_out.name
    ]
    subprocess.run(cmd, check=True)

    return send_file(tmp_out.name, as_attachment=True, download_name="clip.mp4")

@app.route('/')
def home():
    return "FFmpeg API running"

