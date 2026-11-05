#!/usr/bin/env python3
"""Environment check for the video-effects-pack skill. Imports nothing heavy, so it runs even when packages are missing.
Usage: python check_env.py      (exit code 0 = ready, 1 = something is missing; every problem is explained in plain words)"""
import os, shutil, sys

def main():
    here = os.path.dirname(os.path.abspath(__file__)); ok = True
    print("Python %s (%s)" % (sys.version.split()[0], sys.executable))
    if sys.version_info < (3, 9): ok = False; print("PROBLEM  Python 3.9 or newer is required")
    for mod, pip in (("numpy", "numpy"), ("cv2", "opencv-python"), ("PIL", "pillow")):
        try:
            m = __import__(mod); print("OK       %-6s %s" % (mod, getattr(m, "__version__", "")))
        except Exception:
            ok = False; print("MISSING  %-6s -> install with:  %s -m pip install %s" % (mod, os.path.basename(sys.executable) or "python", pip))
    for exe in ("ffmpeg", "ffprobe"):
        p = shutil.which(exe)
        if p: print("OK       %-7s %s" % (exe, p))
        else:
            ok = False; print("MISSING  %s -> install FFmpeg and make sure it is in PATH (Windows: winget install ffmpeg | macOS: brew install ffmpeg | Linux: sudo apt install ffmpeg)" % exe)
    for name in ("Inter-Black.otf", "Inter-Bold.otf", "Inter-Regular.otf", "face_detection_yunet_2023mar.onnx", "haarcascade_frontalface_default.xml", "u2netp.onnx"):
        p = os.path.join(here, "..", "assets", name)
        if os.path.isfile(p) and os.path.getsize(p) > 1000: print("OK       asset %s" % name)
        else: ok = False; print("MISSING  asset %s (the whole assets/ folder must stay next to scripts/)" % name)
    try:
        import cv2
        if not hasattr(cv2, "FaceDetectorYN"): print("NOTE     this OpenCV has no FaceDetectorYN: face finding falls back to the bundled Haar cascade")
    except Exception: pass
    print("READY: all effects can run." if ok else "NOT READY: fix the lines marked MISSING/PROBLEM above, then run this check again.")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
