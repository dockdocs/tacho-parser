#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile

from flask import Flask, jsonify, request

app = Flask(__name__)

API_KEY = os.environ.get("TACHO_PARSER_KEY", "")
READER_DIR = os.environ.get("READER_DIR", "/app/reader")
MAX_BYTES = 16 * 1024 * 1024
TIMEOUT_SEC = 120


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/parse")
def parse():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded (field 'file' required)"}), 400

    upload = request.files["file"]
    data = upload.read()
    if not data:
        return jsonify({"error": "Empty file"}), 400
    if len(data) > MAX_BYTES:
        return jsonify({"error": "File too large"}), 413

    suffix = os.path.splitext(upload.filename or "")[1] or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    out_path = tmp_path + ".json"

    try:
        proc = subprocess.run(
            ["python", "-m", "app.cli", tmp_path, "--json", out_path, "-q"],
            cwd=READER_DIR,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
        )
        if proc.returncode != 0:
            return jsonify({
                "error": "Parser failed",
                "stderr": (proc.stderr or "")[-2000:],
                "stdout": (proc.stdout or "")[-2000:],
            }), 502

        with open(out_path, "r", encoding="utf-8") as jf:
            result = json.load(jf)
        return jsonify(result), 200

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Parser timed out"}), 504
    finally:
        for p in (tmp_path, out_path):
            try:
                os.remove(p)
            except OSError:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
