from bpm_detector import detect_bpm_details
import os

files = [
    ("175 - Annix - Millionaire.flac", 175),
    ("132 - Mathame - Lose Yourself.m4a", 132),
]

for filename, expected in files:
    if os.path.exists(filename):
        print(f"Analyzing {filename}...")
        # We'll temp modify detect_bpm_details to return more info if needed
        # or just trust the current output for now but add a print in the detector
        result = detect_bpm_details(filename)
        print(f"  Expected: {expected} BPM")
        print(f"  Found:    {result['bpm']:.2f} BPM")
    else:
        print(f"File not found: {filename}")
