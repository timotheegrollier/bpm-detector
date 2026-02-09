#!/usr/bin/env python3
"""Detect BPM (tempo) of an audio file using ffmpeg + librosa.

Usage:
  python bpm_detect.py /path/to/audio
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from bpm_detector import detect_bpm_details


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect BPM (tempo) of an audio file.")
    parser.add_argument("input", help="Path to the audio file")
    parser.add_argument(
        "--sr",
        type=int,
        default=22050,
        help="Sample rate used for analysis (default: 22050)",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=None,
        help="Start time in seconds (optional)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Duration in seconds to analyze (optional)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of plain text",
    )
    parser.add_argument(
        "--variations",
        action="store_true",
        help="Show tempo variations",
    )
    parser.add_argument(
        "--variation-threshold",
        type=float,
        default=3.0,
        help="Minimum BPM change to count as a variation (default: 3.0)",
    )
    parser.add_argument(
        "--min-segment",
        type=float,
        default=6.0,
        help="Minimum segment duration in seconds (default: 6.0)",
    )
    parser.add_argument(
        "--smooth",
        type=int,
        default=9,
        help="Median smoothing window in frames (default: 9)",
    )
    parser.add_argument(
        "--hop-length",
        type=int,
        default=96,
        help="Hop length for analysis (default: 96)",
    )
    parser.add_argument(
        "--min-bpm",
        type=float,
        default=60.0,
        help="Minimum BPM to consider (default: 60)",
    )
    parser.add_argument(
        "--max-bpm",
        type=float,
        default=200.0,
        help="Maximum BPM to consider (default: 200)",
    )
    parser.add_argument(
        "--no-hpss",
        action="store_true",
        help="Disable percussive separation (HPSS)",
    )
    parser.add_argument(
        "--no-snap",
        action="store_true",
        help="Disable BPM snapping to neat values",
    )
    parser.add_argument(
        "--snap-tolerance",
        type=float,
        default=0.25,
        help="Snap to nearest BPM if within this tolerance (default: 0.25)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = os.path.abspath(args.input)

    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        details = detect_bpm_details(
            input_path,
            sample_rate=args.sr,
            start=args.start,
            duration=args.duration,
            hop_length=args.hop_length,
            smooth_window=args.smooth,
            change_threshold=args.variation_threshold,
            min_segment_duration=args.min_segment,
            min_bpm=args.min_bpm,
            max_bpm=args.max_bpm,
            use_hpss=not args.no_hpss,
            snap_bpm=not args.no_snap,
            snap_tolerance=args.snap_tolerance,
        )

        bpm = details["bpm"]
        sr = details["sample_rate"]
        segments = details.get("segments", [])

        if args.json:
            seg_out = [
                {
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "bpm": round(seg["bpm"], 2),
                }
                for seg in segments
            ]
            payload = {"bpm": round(bpm, 2), "sample_rate": sr, "segments": seg_out}
            print(json.dumps(payload, ensure_ascii=False, allow_nan=False))
        else:
            print(f"BPM: {bpm:.2f}")
            if args.variations or len(segments) > 1:
                if len(segments) <= 1:
                    print("Variations: none (tempo stable)")
                else:
                    print("Variations:")
                    for seg in segments:
                        print(
                            f"- {seg['start']:.2f}s - {seg['end']:.2f}s: "
                            f"{seg['bpm']:.2f} BPM"
                        )

        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
