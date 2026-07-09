"""SafetyNet TTS Engine — most human-like local AI voice.

Uses Microsoft Neural TTS via edge-tts with zero post-processing
artifacts. Simple, clean, natural.
"""

import asyncio, os, shutil
from pathlib import Path
import edge_tts

VOICES = {
    "jenny": "en-US-JennyNeural",       # Warm female, clearest
    "aria": "en-US-AriaNeural",         # Expressive female
    "guy": "en-US-GuyNeural",           # Natural male
    "christopher": "en-US-ChristopherNeural", # Warm male
    "sonia": "en-GB-SoniaNeural",       # British female
    "ryan": "en-GB-RyanNeural",         # British male
    "natasha": "en-AU-NatashaNeural",   # Australian female
    "neerja": "en-IN-NeerjaExpressiveNeural", # Very expressive female
    "brian": "en-US-BrianNeural",       # Natural male
    "andrew": "en-US-AndrewNeural",     # Calm male
}

# Minimal rate adjustments — just enough for natural pacing
STYLES = {
    "default":   {"rate": "+0%",  "pitch": "+0Hz"},
    "warm":      {"rate": "-2%",  "pitch": "+8Hz"},
    "natural":   {"rate": "-1%",  "pitch": "+3Hz"},
    "smooth":    {"rate": "-3%",  "pitch": "+5Hz"},
    "bright":    {"rate": "+3%",  "pitch": "+12Hz"},
    "deep":      {"rate": "-1%",  "pitch": "-10Hz"},
}


class SafetyNetTTS:
    """Local TTS — clean Microsoft Neural voices, no artifacts."""

    def __init__(self, voice: str = "jenny", style: str = "natural"):
        voice_name = VOICES.get(voice, voice)
        self.voice = voice_name
        cfg = STYLES.get(style, STYLES["default"])
        self.rate = cfg["rate"]
        self.pitch = cfg["pitch"]
        self._tmp = Path("/tmp/safetynet_tts")
        self._tmp.mkdir(parents=True, exist_ok=True)

    async def speak(self, text: str, output: str = None,
                    voice: str = None, style: str = None) -> str:
        """Generate speech. Clean, no post-processing."""
        if not text or not text.strip():
            return None
        voice = VOICES.get(voice, voice) or self.voice
        cfg = STYLES.get(style, STYLES["default"]) if style else STYLES["default"]
        rate, pitch = cfg["rate"], cfg["pitch"]
        # Override with instance defaults if no style override
        if not style:
            rate, pitch = self.rate, self.pitch
        if output is None:
            output = str(self._tmp / f"out_{abs(hash(text))}.mp3")
        try:
            comm = edge_tts.Communicate(
                text, voice=voice,
                rate=rate, pitch=pitch
            )
            await comm.save(output)
            if os.path.getsize(output) < 100:
                return None
            return output
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    async def narrate_script(self, segments: list, output: str = "narration.wav",
                              voice: str = None) -> str:
        """Generate narration from [(text, style), ...] segments."""
        voice = voice or self.voice
        audio_files = []
        for i, (text, style) in enumerate(segments):
            seg_out = str(self._tmp / f"seg_{i:03d}.mp3")
            result = await self.speak(text, output=seg_out, voice=voice, style=style)
            if result:
                audio_files.append(result)

        if not audio_files:
            return None

        import soundfile as sf
        import numpy as np
        combined = []
        for f in audio_files:
            y, sr = sf.read(f)
            combined.append(y)
            combined.append(np.zeros(int(0.2 * sr)))

        full = np.concatenate(combined)
        sf.write(output, full, sr)
        return output

    async def generate_demo_narration(self, output: str = "safetynet_narration.wav",
                                       voice: str = None) -> str:
        voice = voice or self.voice
        script = [
            ("DeFi moves 24/7. Human traders can't watch the markets all the time. Emotional decisions lead to poor outcomes. And cloud-based AI agents are a security nightmare for crypto custody. If the API goes down, rate limits hit, or censorship kicks in, the agent dies. And giving a cloud API access to your wallet is terrifying. Meet SafetyNet.", "natural"),
            ("SafetyNet is the first completely sovereign AI agent built for the Casper Network. Five specialized neural networks run entirely on your local CPU. Zero API calls. Zero internet dependency. Zero data leakage. Every decision stays on your machine.", "natural"),
            ("The architecture has five layers. The Observer polls all Casper data sources, pools, lending markets, volatility, and network congestion. This feeds into the AI Engine, five local neural networks working in parallel.", "smooth"),
            ("MarketRegimeNN classifies the market as bullish, bearish, volatile, or neutral. YieldPredictorNN forecasts APR for every opportunity. RiskScorerNN assigns a 0 to 1 risk score. StrategySelectorNN picks the best strategy from five options. And StrategyReasoner generates natural language explanations of every decision.", "smooth"),
            ("The chosen strategy goes through the Risk Engine, multi-layer guardrails checking slippage, impermanent loss, contract whitelists, and circuit breakers. Safe strategies go to the Transaction Orchestrator for priority batching and gas optimized execution. Every decision is recorded on the AgentVault smart contract on Casper Testnet.", "professional"),
            ("But here is what makes SafetyNet truly unique on Casper. On Ethereum, giving an AI agent control of your wallet means risking your entire balance. Smart contracts hold custody, and one compromised approval equals total loss. On Casper, our session-only AgentVault contract uses Casper's separate session code model. The agent can sign yield routing actions without ever holding custody of your main account. Autonomous trading that is actually safe. This is only possible on Casper.", "warm"),
            ("We also open-sourced a 12 tool MCP server so that any future AI developer on Casper can build their own agents on our infrastructure. Read balances, query pools, check volatility, estimate gas, execute x402 payments, simulate swaps. All through a standard protocol. We did not just build an app. We built infrastructure for the Casper AI ecosystem.", "professional"),
            ("Seven deployable sub-agents coordinate across three topologies. Sequential, parallel, and consensus. Each can be deployed or undeployed independently from the dashboard. You can watch the agent pipeline animate in real time as data packets flow between them.", "natural"),
            ("The dashboard shows everything in real time. Five neural network confidence gauges with glow effects. An animated sub-agent pipeline with flowing data packets. Paper trading with Sharpe ratio, max drawdown, win streaks, and equity curves. A competition comparison tab against all 13 other BUIDLs. And a full x402 micropayment timeline.", "bright"),
            ("SafetyNet. Sovereign AI for the Casper Network. Zero cloud APIs. One hundred percent local CPU execution. Five neural networks. Seven sub-agents. One deployed on-chain contract. Built for the Casper Agentic Buildathon 2026.", "smooth"),
        ]
        return await self.narrate_script(script, output, voice)


# ─── SYNC HELPERS ──────────────────────────────────────

def tts(text: str, voice: str = "jenny", style: str = "natural",
        output: str = None) -> str:
    engine = SafetyNetTTS(voice=voice, style=style)
    return asyncio.run(engine.speak(text, output=output))


def list_voices():
    return list(VOICES.keys())


if __name__ == "__main__":
    import sys
    voice = sys.argv[1] if len(sys.argv) > 1 else "jenny"
    style = sys.argv[2] if len(sys.argv) > 2 else "natural"
    text = " ".join(sys.argv[3:]) or "Hello, I am SafetyNet. An autonomous AI agent with five neural networks. Zero cloud APIs."
    out = tts(text, voice=voice, style=style)
    if out:
        sz = os.path.getsize(out)
        dur = sz / 16000  # rough
        print(f"Generated: {out} ({sz/1024:.0f} KB, ~{dur:.0f}s)")
    else:
        print("Failed")
