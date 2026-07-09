#!/usr/bin/env python3
"""Generate SafetyNet narration using Deepgram Aura-2 TTS.

Usage:
    export DEEPGRAM_API_KEY=your_key_here
    python3 agent/generate_deepgram.py [voice=aura-stella-en] [output.mp3]

Voices: aura-stella-en, aura-athena-en, aura-hera-en, aura-orion-en, aura-arcas-en
"""

import os, sys, json
from pathlib import Path
import requests

# ─── CONVERSATIONAL SCRIPT ──────────────────────────────
# This script sounds like a person talking, not a press release.
# Shorter sentences, natural pauses, conversational tone.

SCRIPT = """Alright, so here is the problem with DeFi today. It runs 24/7. But humans... we sleep. We get emotional. We make bad calls. And handing your wallet keys to some cloud AI? That is terrifying.

So I built SafetyNet. It is an autonomous yield routing agent that runs entirely on your local machine. Five neural networks. Seven sub-agents. Zero cloud API calls. Every decision stays on your computer. Not on OpenAI's servers. Not on some cloud. On your machine.

Here is how it works. MarketRegimeNN looks at the market and decides if it is bullish, bearish, or volatile. YieldPredictorNN forecasts APR. RiskScorerNN assigns a risk score. StrategySelectorNN picks the best move. And StrategyReasoner explains every decision in plain English. All five models run in about four milliseconds on your CPU.

The strategy goes through a risk engine that checks slippage, impermanent loss, contract whitelists, and circuit breakers. Only safe trades get executed.

But here is the part I am most proud of. On Ethereum, giving an AI agent wallet access means risking your entire balance. One compromised approval and you are drained. On Casper, our AgentVault contract uses Casper's session code model. The agent can route yield between pools without ever holding custody of your main account. This literally only works on Casper.

We also built a twelve tool MCP server and open sourced it. Any developer building on Casper can use it.

The dashboard shows everything in real time. Confidence gauges for all five neural networks. Paper trading with Sharpe ratio and equity curves. A competition comparison table showing how we stack up against every other BUIDL.

Five neural networks. Seven sub-agents. One on-chain contract. Zero cloud APIs. SafetyNet. Built for the Casper Agentic Buildathon 2026. And it all runs on your machine."""


def generate(voice: str = "aura-stella-en", output: str = None) -> str:
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        print("ERROR: Set DEEPGRAM_API_KEY environment variable")
        sys.exit(1)

    if output is None:
        vname = voice.replace("aura-", "").replace("-en", "").title()
        output = f"SafetyNet_Narration_Deepgram_{vname}.mp3"

    output_path = Path(__file__).parent.parent / output

    print(f"Generating conversational narration with Deepgram voice '{voice}'...")
    print(f"  Script length: {len(SCRIPT)} chars")
    print(f"  Output: {output_path}")

    url = f"https://api.deepgram.com/v1/speak?model={voice}"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json={"text": SCRIPT}, headers=headers, timeout=120)

    if not resp.ok:
        print(f"HTTP Error {resp.status_code}: {resp.text}")
        sys.exit(1)

    with open(output_path, "wb") as f:
        f.write(resp.content)

    size = os.path.getsize(output_path)
    dur = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
        capture_output=True, text=True
    ).stdout.strip()

    print(f"\nDone: {output_path} ({size/1024:.0f} KB, ~{float(dur or 0):.0f}s)")
    return str(output_path)


if __name__ == "__main__":
    import subprocess
    voice = sys.argv[1] if len(sys.argv) > 1 else "aura-stella-en"
    output = sys.argv[2] if len(sys.argv) > 2 else None
    generate(voice, output)
