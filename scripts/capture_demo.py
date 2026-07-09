#!/usr/bin/env python3
"""Record SafetyNet auto-demo at 10fps — real headed browser for perfect rendering.

Uses Playwright in headed mode (full GPU, proper font anti-aliasing)
and captures frames at 10fps for smooth 1080p60 output.

Usage:
    python3 scripts/capture_demo.py [--duration 55] [--output demo.mp4]

Start the server first:
    python3 agent/api_server.py
"""

import asyncio, argparse, os, subprocess, tempfile, shutil
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(__file__).parent.parent


async def capture_demo(duration: int = 55, output: str = "SafetyNet_Demo_Live.mp4"):
    output_path = OUTPUT_DIR / output
    frames_dir = Path(tempfile.mkdtemp(prefix="safetynet_cap_")) / "frames"
    frames_dir.mkdir(parents=True)
    print(f"Recording {duration}s demo at 10fps headed browser -> {output_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # REAL browser with GPU rendering!
            args=[
                "--no-sandbox",
                "--autoplay-policy=no-user-gesture-required",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,  # Retina rendering
            locale="en-US",
            color_scheme="dark",
        )
        page = await context.new_page()

        print("  Opening dashboard...")
        try:
            await page.goto("http://localhost:5100", wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"  Navigation warning: {e}")

        # Wait for splash
        print("  Waiting for splash + auto-demo start...")
        await asyncio.sleep(3)

        # Capture frames at 10fps with Retina 2x resolution
        fps = 10
        total_frames = duration * fps
        digits = len(str(total_frames))
        print(f"  Capturing {total_frames} frames at {fps}fps...")

        for i in range(total_frames):
            t0 = asyncio.get_event_loop().time()
            frame_path = frames_dir / f"frame_{i:0{digits}d}.png"
            # Capture at full device pixels (3840x2160) for supersampling
            await page.screenshot(path=str(frame_path), full_page=False, type="jpeg", quality=98)
            elapsed = asyncio.get_event_loop().time() - t0
            if i % 50 == 0:
                print(f"    frame {i}/{total_frames} ({elapsed*1000:.0f}ms)")
            await asyncio.sleep(max(0, 1/fps - elapsed))

        await context.close()
        await browser.close()

    # Build 1080p30 video — scale 3840x2160 -> 1920x1080 with Lanczos
    print("  Building 1080p30 video (Lanczos, 25 Mbps)...")
    pattern = str(frames_dir / f"frame_%0{digits}d.jpg")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "h264_videotoolbox",
        "-b:v", "25M",
        "-quality", "highest",
        "-profile", "high",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:flags=lanczos",
        "-movflags", "+faststart",
        "-r", "30",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=300)

    size = os.path.getsize(output_path)
    print(f"\nDone: {output_path} ({size/1024/1024:.1f} MB)")

    try:
        dur = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
            capture_output=True, text=True
        ).stdout.strip()
        if dur:
            print(f"  Duration: {float(dur):.1f}s")
    except:
        pass

    try:
        shutil.rmtree(str(frames_dir.parent))
    except:
        pass

    return str(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=55)
    parser.add_argument("--output", type=str, default="SafetyNet_Demo_Live.mp4")
    args = parser.parse_args()

    result = asyncio.run(capture_demo(args.duration, args.output))
    print(f"Video saved: {result}")
