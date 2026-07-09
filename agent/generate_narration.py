#!/usr/bin/env python3
"""Generate a single continuous narration MP3 — no segment stitching artifacts.

Usage:
    python generate_narration.py [voice] [output.mp3]

Voices: aria (best), jenny (clearest), guy, neerja, etc.
"""

import asyncio, sys, os
import edge_tts


NARRATION = """DeFi moves 24/7. Human traders can't watch the markets all the time. Emotional decisions lead to poor outcomes. And cloud-based AI agents are a security nightmare for crypto custody. Meet SafetyNet.

SafetyNet is the first completely sovereign AI agent built for the Casper Network. Five specialized neural networks run entirely on your local CPU. Zero API calls. Zero internet dependency. Every decision stays on your machine.

The architecture has five layers. MarketRegimeNN classifies the market as bullish, bearish, volatile, or neutral. YieldPredictorNN forecasts APR for every opportunity. RiskScorerNN assigns a zero to one risk score. StrategySelectorNN picks the best strategy from five options. And StrategyReasoner generates natural language explanations of every decision.

The chosen strategy goes through multi-layer risk guardrails checking slippage, impermanent loss, contract whitelists, and circuit breakers. Safe strategies are executed through a priority-batched, gas-optimized transaction orchestrator.

But here is what makes SafetyNet truly unique on Casper. Our session-only AgentVault contract uses Casper's separate session code model. The agent can sign yield routing actions without ever holding custody of your main account. Autonomous trading that is actually safe. This is only possible on Casper.

We also open-sourced a twelve-tool MCP server so that any future AI developer on Casper can build their own agents on our infrastructure. Seven deployable sub-agents coordinate across three topologies: sequential, parallel, and consensus.

The dashboard shows everything in real time. Five neural network confidence gauges with glow effects. An animated sub-agent pipeline with flowing data packets. Paper trading with Sharpe ratio, max drawdown, win streaks, and equity curves. And a full x402 micropayment timeline.

SafetyNet. Sovereign AI for the Casper Network. Zero cloud APIs. One hundred percent local CPU execution. Five neural networks. Seven sub-agents. One deployed on-chain contract. Built for the Casper Agentic Buildathon 2026."""


async def generate(voice: str = "en-US-AriaNeural", output: str = "narration.mp3") -> str:
    print(f"Generating narration with {voice}...")
    comm = edge_tts.Communicate(NARRATION, voice=voice)
    await comm.save(output)
    size = os.path.getsize(output)
    print(f"Saved: {output} ({size/1024:.0f} KB)")
    return output


if __name__ == "__main__":
    voices = {"aria": "en-US-AriaNeural", "jenny": "en-US-JennyNeural",
              "guy": "en-US-GuyNeural", "neerja": "en-IN-NeerjaExpressiveNeural"}
    v = sys.argv[1] if len(sys.argv) > 1 else "aria"
    voice = voices.get(v, v)
    out = sys.argv[2] if len(sys.argv) > 2 else f"SafetyNet_Narration_{v.title()}.mp3"
    asyncio.run(generate(voice, out))
