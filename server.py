# server.py
from flask import Flask, request, send_file, jsonify
import subprocess, tempfile, requests, os

# -----------------------------
# Initialize Flask app
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Root route (for Render health check)
# -----------------------------
@app.route('/')
def home():
    return jsonify({"status": "running", "message": "FFmpeg API live"})

# -----------------------------
# FFmpeg trim endpoint
# -----------------------------
@app.route('/trim', methods=['POST'])
def trim():
    try:
        data = request.get_json(force=True)
        url = data.get('video_url')
        start = data.get('start')
        duration = data.get('duration') or (
            data.get('end') and (float(data.get('end')) - float(start))
        )

        if not url or start is None or duration is None:
            return jsonify({
                "error": "video_url, start, and duration (or end) required"
            }), 400

        print(f"[DEBUG] Downloading video from: {url}", flush=True)

        # Create temporary files
        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_in.close()
        tmp_out.close()

        print(f"[DEBUG] Temp input file: {tmp_in.name}")
        print(f"[DEBUG] Temp output file: {tmp_out.name}")

        # Download input video
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(tmp_in.name, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        print("[DEBUG] Download complete. Running FFmpeg...", flush=True)

        # Run FFmpeg trim (fast copy)
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-ss", str(start),
            "-t", str(duration),
            "-i", tmp_in.name,
            "-c", "copy",
            tmp_out.name,
        ]

        print(f"[DEBUG] Running command: {' '.join(cmd)}", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True)

        print(f"[DEBUG] FFmpeg return code: {result.returncode}")
        if result.stderr:
            print(f"[DEBUG] FFmpeg stderr: {result.stderr}", flush=True)
        if result.stdout:
            print(f"[DEBUG] FFmpeg stdout: {result.stdout}", flush=True)

        if result.returncode != 0:
            return jsonify({
                "error": "FFmpeg failed",
                "stderr": result.stderr
            }), 500

        print("[DEBUG] FFmpeg succeeded. Sending file to user...", flush=True)
        return send_file(tmp_out.name, as_attachment=True, download_name="clip.mp4")

    except requests.RequestException as e:
        print(f"[DEBUG] Download error: {str(e)}", flush=True)
        return jsonify({"error": "Download failed", "details": str(e)}), 500
    except subprocess.CalledProcessError as e:
        print(f"[DEBUG] FFmpeg error: {str(e)}", flush=True)
        return jsonify({"error": "FFmpeg failed", "details": str(e)}), 500
    except Exception as e:
        print(f"[DEBUG] Unexpected error: {str(e)}", flush=True)
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500


# -----------------------------
# FFmpeg installation check
# -----------------------------
@app.route('/check_ffmpeg')
def check_ffmpeg():
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return jsonify({"ok": True, "output": result.stdout.split("\n")[0]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# -----------------------------
# Local run (for testing)
# -----------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)



