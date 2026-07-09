#!/usr/bin/env python3
"""Build SafetyNet demo FINAL — 4K, variable 5-15s scenes, high quality.

Scenes:
  - Intro/outro: 5s (just branding, no reading)
  - BTS visualizations: 10-15s (data to absorb)
  - Terminal action: 15s (lots of text)
  - Dashboard scenes: 10s (some numbers)
Output: 3840x2160 (4K UHD), CRF 14, slow preset
"""

import asyncio, subprocess, os, tempfile, shutil
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(__file__).parent.parent
MUSIC = OUTPUT_DIR / "music_embrace.mp3"
OUT_W, OUT_H = 3840, 2160  # 4K
FPS = 30

# (scene, duration_seconds)
SCENES = [
    ({"type": "card", "text": "SafetyNet", "sub": "Autonomous Yield Routing Agent\nZero Cloud APIs · 100% Local CPU", "color": "#00d4aa"}, 4),

    ({"type": "bts", "file": "behind_terminal.html"}, 10),

    ({"type": "bts", "file": "behind_neural.html"}, 8),

    ({"type": "dash", "tab": "ai"}, 8),

    ({"type": "bts", "file": "behind_pipeline.html"}, 8),

    ({"type": "dash", "tab": "overview"}, 8),

    ({"type": "bts", "file": "behind_risk.html"}, 8),

    ({"type": "dash", "tab": "risk"}, 8),

    ({"type": "bts", "file": "behind_x402.html"}, 8),

    ({"type": "dash", "tab": "paper"}, 8),

    ({"type": "dash", "tab": "agents"}, 8),

    ({"type": "dash", "tab": "mcp"}, 8),

    ({"type": "dash", "tab": "competition"}, 8),

    ({"type": "card", "text": "SafetyNet", "sub": "5 Neural Networks · 7 Sub-Agents\ngithub.com/DaMaker1291/SafetyNet", "color": "#a855f7"}, 4),
]


def make_title_card(text, sub, color, duration, out_path):
    lines = [text] + sub.split("\n")
    y = 700  # higher for 4K
    text_filters = []
    for i, line in enumerate(lines):
        if i == 0:
            fs, fc = 144, color        # big for 4K
        elif i == 1:
            fs, fc = 56, "#a855f7"
        else:
            fs, fc = 32, "#586078"
        text_filters.append(
            f"drawtext=text='{line}':fontcolor={fc}:fontsize={fs}"
            f":fontfile=/System/Library/Fonts/Helvetica.ttc"
            f":x=(w-text_w)/2:y={y}"
        )
        y += fs + 50
    vf = ",".join(text_filters)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#02050e:s={OUT_W}x{OUT_H}:d={duration}:r={FPS}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)


async def capture_all():
    work = Path(tempfile.mkdtemp(prefix="safetynet_final_"))
    shots = work / "shots"
    shots.mkdir()

    print("Capturing screenshots (headed browser, 4K Retina)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},  # CSS pixels
            device_scale_factor=2,  # 2x = 3840x2160 actual pixels
            locale="en-US", color_scheme="dark",
        )
        page = await ctx.new_page()

        # Load dashboard ONCE, skip splash
        await page.goto("http://localhost:5100", wait_until="networkidle", timeout=15000)
        await asyncio.sleep(5)  # wait for splash + init

        for i, (scene, dur) in enumerate(SCENES):
            shot = shots / f"scene_{i:02d}.png"
            if scene["type"] == "card":
                continue

            if scene["type"] == "bts":
                url = f"file://{OUTPUT_DIR / 'frontend' / scene['file']}"
                await page.goto(url, wait_until="networkidle", timeout=10000)
                await asyncio.sleep(0.5)
                await page.screenshot(path=str(shot), full_page=False)

            elif scene["type"] == "dash":
                # Navigate back to dashboard if we were on a BTS page
                if page.url.startswith("file://"):
                    await page.goto("http://localhost:5100", wait_until="networkidle", timeout=15000)
                    await asyncio.sleep(1)
                # Tab switch — no page reload if already on dashboard
                await page.evaluate(f"switchTab('{scene['tab']}')")
                await asyncio.sleep(0.8)
                await page.screenshot(path=str(shot), full_page=False)

            label = scene.get("tab", scene.get("file", scene.get("text", "?")))
            print(f"  [{i+1}/{len(SCENES)}] {label} ({dur}s)")

        await ctx.close()
        await browser.close()

    return work


def build_video(work, output_path):
    shots = work / "shots"
    scenes_dir = work / "scenes"
    scenes_dir.mkdir()
    concat_file = work / "concat.txt"

    print("\nBuilding 4K scenes (slow preset, high quality)...")
    scene_files = []
    total_dur = 0

    for i, (scene, dur) in enumerate(SCENES):
        scene_out = scenes_dir / f"scene_{i:02d}.mp4"
        total_dur += dur

        if scene["type"] == "card":
            make_title_card(scene["text"], scene["sub"], scene["color"], dur, scene_out)
            scene_files.append(scene_out)
            print(f"  Scene {i}: {dur}s — {scene['text']}")
            continue

        shot = shots / f"scene_{i:02d}.png"
        if not shot.exists():
            continue

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(shot),
            "-c:v", "libx264", "-t", f"{dur}",
            "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={OUT_W}:{OUT_H}",
            str(scene_out),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        scene_files.append(scene_out)
        label = scene.get("tab", scene.get("file", "?").replace("behind_","").replace(".html",""))
        print(f"  Scene {i}: {dur}s — {label}")

    # Concatenate
    print(f"\nConcatenating {len(scene_files)} scenes ({total_dur}s total)...")
    with open(concat_file, "w") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")

    video_only = work / "video_only.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(video_only),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)

    # Add background music — boosted volume
    print(f"\nAdding background music ({total_dur}s, volume boosted)...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_only),
        "-stream_loop", "-1", "-i", str(MUSIC),
        "-filter_complex",
        f"[1:a]volume=2.0,afade=t=in:st=0:d=2,afade=t=out:st={total_dur - 3}:d=3,alimiter=limit=0.9:attack=5:release=50[m]",
        "-map", "0:v", "-map", "[m]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)

    size = os.path.getsize(output_path)
    print(f"\nFinal: {output_path}")
    print(f"  Resolution: {OUT_W}x{OUT_H} (4K UHD)")
    print(f"  Duration: {total_dur}s ({total_dur/60:.1f} min)")
    print(f"  Size: {size/1024/1024:.1f} MB")
    print(f"  Scenes: {len(scene_files)}")


async def main():
    try:
        r = subprocess.run(["curl", "-s", "--connect-timeout", "2",
                           "http://localhost:5100/api/status"],
                          capture_output=True, text=True, timeout=5)
        if not r.stdout:
            print("Server not running! Start: python3 agent/api_server.py")
            return
    except:
        print("Server not running! Start: python3 agent/api_server.py")
        return

    if not MUSIC.exists():
        print("Music not found!")
        return

    work = await capture_all()
    output = OUTPUT_DIR / "SafetyNet_Final_4K.mp4"
    build_video(work, output)

    try:
        shutil.rmtree(str(work))
    except:
        pass

    print("\nDone! Upload to YouTube unlisted + submit to DoraHacks.")


if __name__ == "__main__":
    asyncio.run(main())
