# SafetyNet — Demo Video Script (Updated)
**Duration**: ~8 minutes | **Resolution**: 1920×1080 | **Audio**: Clear narration + low background music

---

## 0. Pre-Recording Checklist
- [ ] `python3 agent/api_server.py` running on localhost:5100
- [ ] Dashboard open in Chrome fullscreen at http://localhost:5100
- [ ] Terminal window with `./scripts/deploy_contract.sh init` ready (or use existing hashes)
- [ ] OBS / QuickTime set to record full screen at 1920×1080
- [ ] Microphone tested, captions template ready

---

## 1. Opening (0:00–0:45)

**[Visual: Dashboard loading → AI model cards animate in one by one]**
**[Audio: Upbeat tech background music, fade under narration]**

**Narrator:**
"Meet SafetyNet — the first fully autonomous AI agent framework built for the Casper Network. SafetyNet uses five locally-running neural networks to continuously monitor the Casper ecosystem, analyze market conditions, generate DeFi strategies, and record every decision on-chain.

Built for the Casper Agentic Buildathon 2026 at the intersection of Agentic AI, Decentralized Finance, and Real-World Assets."

---

## 2. The Problem (0:45–1:30)

**[Visual: Split screen — left: stressed trader, right: dashboard running smoothly]**

**Narrator:**
"DeFi moves 24/7. Human traders can't watch the markets all the time. Emotional decisions lead to poor outcomes. And once you decide on a strategy, there's no transparent record of why or when it was executed.

SafetyNet solves all of this with an autonomous AI agent that:
- Never sleeps — 24/7 market monitoring across all Casper dApps
- Makes data-driven decisions — five AI models working together, no emotions
- Records everything on-chain — complete transparency and auditability
- Adapts to any market regime — bullish, bearish, or volatile"

---

## 3. Architecture Overview (1:30–2:30)

**[Visual: Animated architecture diagram — flows from Observer → AI Engine → Risk Engine → Orchestrator → On-Chain]**

**Narrator:**
"SafetyNet has five layers, each running on your machine with zero API calls.

First, the **Observer** polls all Casper data sources — pools, lending markets, volatility, and network congestion.

This feeds into the **AI Engine** — five local neural networks working in parallel:
- MarketRegimeNN classifies the market as Bullish, Bearish, Volatile, or Neutral
- YieldPredictorNN forecasts APR for each opportunity
- RiskScorerNN assigns a 0-to-1 risk score
- StrategySelectorNN picks the best strategy from five options
- StrategyReasoner generates natural-language explanations

The chosen strategy goes through the **Risk Engine** — multi-layer guardrails checking slippage, impermanent loss, contract whitelists, and circuit breakers.

Safe strategies go to the **Transaction Orchestrator** for priority batching and gas-optimized execution.

Every decision is recorded on the **AgentVault smart contract** on Casper Testnet.

All of this is visible in real-time on the **dashboard** — which you're looking at right now."

**[Visual: Mouse hovers over the 5 AI model cards, highlighting each one]**

---

## 4. AI Engine Demo (2:30–4:00)

**[Visual: Dashboard — AI Engine tab, click "Run Now"]**

**Narrator:**
"Let's see the AI in action. I'll click 'Run Now' to analyze the current market with all four neural networks.

**[Click button — results animate in]**

The MarketRegimeNN classifies the market as BULLISH with 92% confidence. The StrategySelectorNN recommends Yield Optimization at 77%. The RiskScorerNN rates this as SAFE with a score of 0.12. And the YieldPredictor forecasts 14.5% net APR.

**[Switch to Overview tab]**

Now let's run a full agent cycle. I'll click '1 Cycle'."

**[Click "1 Cycle" — watch the console stream data]**

"The agent polls data, runs all five AI models, evaluates opportunities, checks risk, and generates an allocation plan — all in a few seconds.

You can see the AI reasoning panel at the top right — the StrategyReasoner explains why this strategy was chosen in natural language."

---

## 5. Paper Trading Demo (4:00–5:30)

**[Visual: Switch to "Paper Trading" tab]**

**Narrator:**
"SafetyNet includes a full paper trading engine with simulated P&L tracking. Let's run five cycles to build up some trading history.

**[Click "Batch" with 5 cycles — watch cycles stream in]**

After five cycles, we can see the paper trading metrics:
- **Sharpe ratio** — our risk-adjusted return
- **Max drawdown** — our largest peak-to-trough decline
- **Win rate** and **win streak** — how consistently we profit

**[Point to Equity Curve chart]**

The equity curve shows our capital growing over time. The green line is cumulative P&L, the purple dashed line is total capital.

**[Point to Daily Returns bar chart]**

The bar chart shows each cycle's return — green bars are profitable, red bars are losses.

**[Point to Trade History table]**

The trade history table shows every simulated trade with allocation amounts, return percentages, and P&L in dollars."

---

## 6. On-Chain Contract Demo (5:30–6:45)

**[Visual: Terminal window, deployment in progress]**

**Narrator:**
"SafetyNet has an on-chain component — the AgentVault session contract deployed on Casper Testnet. Every agent registration and strategy submission is recorded as a permanent on-chain transaction.

**[Show deploy_contract.sh running]**

We run `./scripts/deploy_contract.sh init` to initialize on-chain storage — creating dictionary seeds and counters..."

**[Show register_agent command]**

"Then `./scripts/deploy_contract.sh register_agent` to register an agent on-chain. Each transaction is submitted via CSPR.cloud's RPC proxy with authentication.

**[Show transaction hashes]**

Here's the proof: the init transaction `f2247779` cost 0.719 CSPR and succeeded. The register_agent transaction `d69620dd` cost 0.220 CSPR and stored the SafetyNet agent on-chain.

This means every AI agent action can be independently verified on the Casper blockchain."

**[Show Competition tab]**

---

## 7. Competition Comparison (6:45–7:30)

**[Visual: Switch to "🏆 Competition" tab]**

**Narrator:**
"Here's where SafetyNet really stands out. The Competition tab compares SafetyNet against every other BUIDL in the Casper Agentic Buildathon.

SafetyNet is the only entry with:
- **5 local AI models** — everyone else uses Claude/GPT API calls
- **A deployed on-chain contract** — verified on Casper Testnet
- **Paper trading with advanced metrics** — Sharpe ratio, drawdown, win streaks
- **A professional trading terminal dashboard** — AI radar chart, live ticker, 9 feature tabs
- **A multi-layer risk engine** — slippage, IL, whitelist, circuit breakers

**[Scroll through the comparison table]**

The judging advantage section breaks down exactly why SafetyNet excels across all seven judging criteria: Technical Execution, Innovation, AI Usage, Real-World Applicability, UX Design, Smart Contracts, and Launch Plans."

---

## 8. x402 Micropayments (7:30–8:00)

**[Visual: Switch to x402 tab]**

**Narrator:**
"SafetyNet also implements the x402 HTTP-native micropayment protocol, allowing AI agents to pay for data access autonomously.

**[Select a resource, click Pay]**

I'll pay 0.001 CSPR for real-time yield data. The payment is processed instantly, and the data is returned.

**[Show payment timeline]**

The payment history timeline on the right shows all x402 transactions — creating a verifiable record of agent spending.

This positions SafetyNet at the cutting edge of autonomous machine-to-machine commerce on Casper."

---

## 9. Roadmap & Call to Action (8:00–8:30)

**[Visual: Switch to GitHub repo in browser]**

**Narrator:**
"SafetyNet is just getting started. Phase 1 — the Buildathon submission — is complete with a working dashboard, five local AI models, paper trading, x402 payments, and a deployed on-chain contract.

Phase 2 brings mainnet deployment, real Casper DeFi protocol integration, and RWA oracle connectivity.

Phase 3 adds reinforcement learning, DAO governance, and a marketplace for autonomous agent strategies.

All code is open-source on GitHub. Check out the repository, watch the code walkthrough, and see why SafetyNet is the most technically complete submission in this hackathon.

SafetyNet — Autonomous AI for the Casper Network. Thank you."

**[Visual: Fade to SafetyNet logo with "Built for Casper Agentic Buildathon 2026" and GitHub link]**

---

## Production Notes

- **Screen recording**: Use OBS Studio or QuickTime Player at 1920×1080
- **Terminal**: iTerm2 with Dracula theme, font size 11pt
- **Dashboard**: Chrome in fullscreen (Cmd+Shift+F) at http://localhost:5100
- **Audio**: Clear narration + low background music (fade during narration, boost at title card)
- **Captions**: Add English subtitles throughout
- **Thumbnail**: SafetyNet logo on dark background + "5 Local AI Models · Casper DeFi"
- **Submission**: Upload to YouTube (unlisted), paste link in DoraHacks submission form
