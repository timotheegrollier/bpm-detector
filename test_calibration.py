"""Calibration test for BPM detection.

Tests known reference files to ensure the detector returns correct values.
Run with: python test_calibration.py
"""
from bpm_detector import detect_bpm_details

files = [
    ("14Le Roumain - Unsafe Liquids.wav", 113),
    ("16Sagsag23 - Alpha Arietis (Out on Tribal Express 02).wav", 175),
]

all_ok = True
for filename, expected in files:
    try:
        result = detect_bpm_details(filename)
        found = round(result["bpm"])
        status = "✅" if found == expected else "❌"
        print(f"{status} {filename}")
        print(f"   Expected: {expected} BPM")
        print(f"   Found:    {result['bpm']:.2f} BPM")
        if found != expected:
            all_ok = False
    except Exception as e:
        print(f"❌ {filename}")
        print(f"   Error: {e}")
        all_ok = False

print()
if all_ok:
    print("✅ All calibration tests PASSED")
else:
    print("❌ Some calibration tests FAILED")