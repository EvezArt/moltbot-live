#!/usr/bin/env python3
"""
EVEZ VCL Live Stream — Headless Chrome + FFmpeg RTMP Pipeline
Renders the Three.js VCL visualizer in headless Chromium,
captures via virtual framebuffer, streams to YouTube Live.
"""
import os, sys, signal, subprocess, time, atexit, json, shutil

# ── Configuration ──────────────────────────────────────────
DISPLAY = os.environ.get("STREAM_DISPLAY", ":99")
WIDTH = int(os.environ.get("STREAM_WIDTH", "1280"))
HEIGHT = int(os.environ.get("STREAM_HEIGHT", "720"))
FPS = os.environ.get("FPS", "30")
BITRATE = os.environ.get("BITRATE", "2500k")
YOUTUBE_RTMP_URL = os.environ.get("YOUTUBE_RTMP_URL", "rtmp://a.rtmp.youtube.com/live2")
YOUTUBE_STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY", "")
VCL_HTML = os.environ.get("VCL_HTML", "/app/visualizer/index.html")

processes = []

def cleanup():
    for p in processes:
        try: p.terminate(); p.wait(timeout=5)
        except:
            try: p.kill()
            except: pass
    print("[stream] Cleaned up.")

atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda s,f: (cleanup(), sys.exit(0)))
signal.signal(signal.SIGTERM, lambda s,f: (cleanup(), sys.exit(0)))

def start_xvfb():
    print(f"[stream] Starting Xvfb {DISPLAY} @ {WIDTH}x{HEIGHT}...")
    p = subprocess.Popen([
        "Xvfb", DISPLAY, "-screen", "0", f"{WIDTH}x{HEIGHT}x24",
        "-ac", "+extension", "GLX", "+render", "-noreset"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    processes.append(p)
    time.sleep(1)
    if p.poll() is not None:
        print("[stream] ERROR: Xvfb failed!"); sys.exit(1)
    os.environ["DISPLAY"] = DISPLAY
    print(f"[stream] Xvfb OK on {DISPLAY}")
    return p

def start_chromium():
    print("[stream] Starting Chromium...")
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY

    # Find chromium binary
    chrome = None
    for candidate in ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]:
        if shutil.which(candidate):
            chrome = candidate
            break
    if not chrome:
        print("[stream] ERROR: No Chromium found!"); sys.exit(1)

    p = subprocess.Popen([
        chrome,
        "--no-sandbox", "--disable-gpu", "--disable-software-rasterizer",
        "--use-gl=swiftshader",  # Software WebGL
        f"--window-size={WIDTH},{HEIGHT}",
        "--window-position=0,0",
        "--kiosk",  # Fullscreen
        "--disable-extensions",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--autoplay-policy=no-user-gesture-required",
        f"file://{VCL_HTML}"
    ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    processes.append(p)
    time.sleep(3)
    if p.poll() is not None:
        print("[stream] ERROR: Chromium failed!"); sys.exit(1)
    print("[stream] Chromium rendering VCL visualizer.")
    return p

def start_ffmpeg():
    if not YOUTUBE_STREAM_KEY:
        print("[stream] ERROR: YOUTUBE_STREAM_KEY not set!"); sys.exit(1)

    rtmp_url = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"
    print(f"[stream] FFmpeg → {YOUTUBE_RTMP_URL}/***")

    cmd = [
        "ffmpeg", "-y",
        # Video: X11 screen capture
        "-f", "x11grab",
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", FPS,
        "-i", DISPLAY,
        # Audio: silent (YouTube requires audio)
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        # Encoding
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-b:v", BITRATE,
        "-maxrate", BITRATE,
        "-bufsize", f"{int(BITRATE.replace('k',''))* 2}k" if 'k' in BITRATE else BITRATE,
        "-pix_fmt", "yuv420p",
        "-g", str(int(FPS)*2),  # keyframe every 2s
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv",
        rtmp_url
    ]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append(p)
    time.sleep(2)
    if p.poll() is not None:
        stderr = p.stderr.read().decode()
        print(f"[stream] ERROR: FFmpeg failed!\n{stderr}"); sys.exit(1)
    print("[stream] FFmpeg streaming to YouTube Live!")
    return p

def main():
    print("=" * 60)
    print("  EVEZ VCL Live — Cognition Topology Stream")
    print("=" * 60)
    
    xvfb = start_xvfb()
    chrome = start_chromium()
    ffmpeg = start_ffmpeg()
    
    print("\n[stream] ✅ All systems GO. Streaming to YouTube Live.")
    print(f"[stream] Resolution: {WIDTH}x{HEIGHT} @ {FPS}fps")
    print(f"[stream] Bitrate: {BITRATE}")
    
    # Monitor processes
    while True:
        time.sleep(10)
        for name, proc in [("Xvfb", xvfb), ("Chromium", chrome), ("FFmpeg", ffmpeg)]:
            if proc.poll() is not None:
                print(f"[stream] {name} died (exit {proc.returncode}). Restarting everything...")
                cleanup()
                sys.exit(1)  # run_forever.sh will restart

if __name__ == "__main__":
    main()
