#!/usr/bin/env python3
"""Simple web UI for BPM detection."""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from bpm_detector import detect_bpm_details

APP_MAX_MB = 200

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = APP_MAX_MB * 1024 * 1024


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


@app.get("/")
def index():
    return render_template("index.html", max_mb=APP_MAX_MB)


@app.post("/api/analyze")
def analyze():
    if "audio" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["audio"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty file"}), 400

    start = _parse_float(request.form.get("start"))
    duration = _parse_float(request.form.get("duration"))
    sample_rate = _parse_int(request.form.get("sr"), 22050)
    min_bpm = _parse_float(request.form.get("min_bpm"))
    max_bpm = _parse_float(request.form.get("max_bpm"))

    temp_path = None
    try:
        filename = secure_filename(file.filename)
        suffix = os.path.splitext(filename)[1] or ".audio"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            file.save(temp_path)

        details = detect_bpm_details(
            temp_path,
            sample_rate=sample_rate,
            start=start,
            duration=duration,
            min_bpm=min_bpm,
            max_bpm=max_bpm,
        )
        segments = [
            {
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "bpm": round(seg["bpm"], 2),
            }
            for seg in details.get("segments", [])
        ]

        return jsonify(
            {
                "bpm": round(details["bpm"], 2),
                "sample_rate": details["sample_rate"],
                "segments": segments,
            }
        )
    except (RuntimeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
