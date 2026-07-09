#!/usr/bin/env python3
"""Generate SafetyNet narration using ElevenLabs — near-human voiceover.

Usage:
    export ELEVENLABS_API_KEY=your_key_here
    python3 agent/generate_elevenlabs.py [voice=Rachel] [output.mp3]

Free tier: 10,000 chars/month. Our script uses ~1,400 chars.
Best voices (free): Rachel, Adam, Bella, Patrick, Antoni
"""

import os, sys, asyncio, json
from pathlib import Path
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# Concise, punchy ~75s narration for demo video
NARRATION = """DeFi moves 24/7. Human traders can't watch the markets all the time. Emotional decisions lead to poor outcomes. And cloud-based AI agents are a security nightmare for crypto custody.

Meet SafetyNet. The first completely sovereign AI agent for the Casper Network. Five specialized neural networks run entirely on your local CPU. Zero API calls. Zero internet dependency. Every decision stays on your machine.

The AI Engine uses five models working in parallel. MarketRegimeNN classifies the market. YieldPredictorNN forecasts APR. RiskScorerNN assigns risk scores. StrategySelectorNN picks the best strategy. And StrategyReasoner explains every decision in plain language.

The chosen strategy goes through multi-layer risk guardrails checking slippage, impermanent loss, and circuit breakers. Safe strategies are executed through a priority-batched, gas-optimized transaction orchestrator.

But here is what makes SafetyNet truly unique. Our session-only AgentVault contract uses Casper's separate session code model. The agent can sign yield routing actions without ever holding custody of your main account. Autonomous trading that is actually safe. Only possible on Casper.

The dashboard shows everything in real time. Neural network confidence gauges. An animated sub-agent pipeline. Paper trading with Sharpe ratio and equity curves. A full x402 micropayment timeline. And a competition comparison against all other BUIDLs.

SafetyNet. Sovereign AI for the Casper Network. Zero cloud APIs. One hundred percent local CPU. Five neural networks. Seven sub-agents. Built for the Casper Agentic Buildathon 2026."""

# ElevenLabs voice IDs for free tier voices
VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",  # Warm, clear, authoritative — best for demos
    "adam": "pNInz6obpgDQGcFmaJgB",    # Deep male, trustworthy
    "bella": "EXAVITQu4vrVxnwl2lA",    # Bright female, energetic
    "patrick": "ODq5zmih8GrVes37Diz",  # Professional male
    "antoni": "ErXwobaYiN019PkySvjV",  # Neutral male
    "dorothy": "ThT5KcBeYPX3keUQqHPh", # Warm female, calm
}


def generate(voice: str = "rachel", output: str = None) -> str:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: Set ELEVENLABS_API_KEY environment variable")
        print("  Get your free key at https://elevenlabs.io/app/settings/api-keys")
        sys.exit(1)

    voice_id = VOICES.get(voice.lower(), voice)
    if output is None:
        output = f"SafetyNet_Narration_ElevenLabs_{voice.title()}.mp3"

    client = ElevenLabs(api_key=api_key)
    output_path = Path(__file__).parent.parent / output

    print(f"Generating narration with ElevenLabs voice '{voice}' ({voice_id})...")
    print(f"  Script length: {len(NARRATION)} chars")
    print(f"  Output: {output_path}")

    # Use optimized voice settings for natural delivery
    audio_stream = client.text_to_speech.convert(
        text=NARRATION,
        voice_id=voice_id,
        model_id="eleven_flash_v2_5",  # Fastest model, excellent quality
        voice_settings=VoiceSettings(
            stability=0.4,       # Lower = more expressive
            similarity_boost=0.8, # Higher = closer to original voice
            style=0.3,           # Moderate expressiveness
            use_speaker_boost=True,
        ),
    )

    # Write audio to file
    with open(output_path, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)

    size = os.path.getsize(output_path)
    print(f"\nDone: {output_path} ({size/1024:.0f} KB)")
    print(f"  Characters used: ~{len(NARRATION)} / 10,000 free tier")
    return str(output_path)


if __name__ == "__main__":
    voice = sys.argv[1] if len(sys.argv) > 1 else "rachel"
    output = sys.argv[2] if len(sys.argv) > 2 else None
    generate(voice, output)
