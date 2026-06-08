# SafetyNet — Demo Video Script

**Duration**: ~8 minutes

---

## 1. Opening (0:00–0:45)

**[Visual: Logo animation → Dashboard]**
**[Audio: Upbeat tech background music]**

**Narrator:**
"Meet SafetyNet — the first autonomous AI agent framework built for the Casper Network. SafetyNet is an agentic AI system that continuously monitors the Casper ecosystem, analyzes market conditions, generates DeFi strategies, and executes them on-chain — all without human intervention.

Built for the Casper Buildathon 2025 at the intersection of Agentic AI, Decentralized Finance, and Real-World Assets."

---

## 2. The Problem (0:45–1:30)

**[Visual: Split screen — left: human trader stressed, right: dashboard showing 24/7 operation]**

"Narrator:
"DeFi moves 24/7. Human traders can't watch the markets all the time. Emotional decisions lead to poor outcomes. And once you decide on a strategy, there's no transparent record of why or when it was executed.

SafetyNet solves all of this with an autonomous AI agent that:
- Never sleeps — 24/7 market monitoring
- Makes data-driven decisions — no emotions, no bias
- Records everything on-chain — complete transparency
- Adapts to any market regime — bullish, bearish, or volatile"

---

## 3. Architecture Overview (1:30–2:30)

**[Visual: Architecture diagram animating in]**

"Narrator:
"SafetyNet has four layers:

First, the **Market Agent** fetches real-time data — CSPR price from CoinGecko, network stats from the Casper node, on-chain transaction volume, and sentiment signals.

This feeds into the **Strategy Agent**, which uses AI to classify the market regime and rank five strategy types: Yield Optimization, Liquidity Provision, Arbitrage Detection, Risk Rebalancing, and RWA Collateralization.

The chosen strategy goes to the **Execution Agent**, which submits it to our **AgentVault smart contract** on Casper Testnet — permanently recording every decision on-chain.

All of this is visible in real-time on the **web dashboard**."

---

## 4. Smart Contract Demo (2:30–4:30)

**[Visual: Screen recording — terminal showing contract compilation and deployment]**

"Narrator:
"Let's look at the on-chain component. AgentVault is a Rust smart contract compiled to Wasm and deployed on Casper Testnet.

Here we're initializing the contract... creating dictionaries for agents, strategies, and actions.

[Type: casper-client put-deploy...]

The contract has eight entry points:
- `init` — sets up the contract
- `register_agent` — registers an AI agent with a name and description
- `submit_strategy` — stores a strategy with its parameters
- `record_action` — logs every action the agent takes
- And query functions to read the on-chain state

[Visual: Switching to cspr.live explorer showing the deploy]

Here's the deploy on the Casper Testnet explorer — you can see the transaction is confirmed and the contract is live.

Each strategy and action produces a verifiable on-chain record with timestamps and transaction hashes. This means agent accountability is built into the protocol."

---

## 5. AI Agent Demo (4:30–6:30)

**[Visual: Terminal running agent_manager.py]**

"Narrator:
"Now let's see the AI agent in action. We'll run it for three cycles.

[Type: python agent_manager.py 3]

Cycle 1: The Market Agent fetches data — CSPR is at $0.042, sentiment is positive, transaction volume is healthy. The Strategy Agent classifies the market as bullish and recommends Yield Optimization with 92% confidence. The Execution Agent submits this to the smart contract — a transaction hash is generated.

[Visual: Dashboard updating with cycle 1 data]

On the dashboard, we can see the CSPR price chart, the active strategies with their confidence scores, and the on-chain transaction history.

Cycle 2: Market conditions have shifted slightly. The agent detects increased volatility and adjusts — now recommending Arbitrage Detection as the primary strategy. This is recorded on-chain alongside the first strategy.

Cycle 3: The agent runs a full rebalancing — allocating across multiple strategies based on the latest market analysis.

The key insight: every decision is explained, every action is recorded on-chain, and the agent adapts in real-time."

---

## 6. Dashboard Tour (6:30–7:15)

**[Visual: Full screen dashboard, mouse hovering over elements]**

"Narrator:
"The dashboard gives you complete visibility into agent operations.

On the top: key metrics — CSPR price, active strategies, total on-chain actions, and agent confidence score.

The market chart shows 24-hour price action with volume overlay.

The strategy portfolio panel shows all five strategy types with their current confidence scores. The agent dynamically adjusts these based on market conditions.

Below: the on-chain activity table shows every transaction the agent has submitted to Casper Testnet, with type, strategy, and transaction hash.

And the agent decision log streams real-time decisions — market snapshots, strategy inferences, and submission confirmations."

---

## 7. Roadmap & Vision (7:15–7:45)

**[Visual: Roadmap graphic with 3 phases]**

"Narrator:
"This is just the beginning.

Phase 1 is the Buildathon submission — working smart contract, AI agent, and dashboard.

Phase 2: Mainnet deployment, integration with real Casper DeFi protocols like CSPR.fans and CasperSwap, RWA oracle integration, and community voting support.

Phase 3: Reinforcement learning for self-optimizing strategies, decentralized governance via DAO, and an open marketplace where anyone can deploy their own SafetyNet agent.

We're building the autonomous agent layer for the Casper ecosystem."

---

## 8. Call to Action (7:45–8:00)

**[Visual: Logo + links]**

"Narrator:
"Check out our GitHub repo for the full source code. Vote for us on CSPR.fans. Join our Discord to be part of the journey.

SafetyNet — Autonomous AI for the Casper Network.

Thank you."

**[Visual: Fade to black with "SafetyNet" logo and "Built for Casper Buildathon 2025"]**

---

## Production Notes

- **Screen resolution**: Record at 1920×1080
- **Terminal font**: Use a monospace font with dark theme (e.g., iTerm2 + Dracula)
- **Dashboard**: Open `frontend/index.html` in Chrome in fullscreen
- **Audio**: Clear narration + low background music (fade during narration)
- **Captions**: Add English subtitles
- **Thumbnail**: SafetyNet logo on dark background with "AI Agent for Casper DeFi"
