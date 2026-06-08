# AETHOS — Autonomous AI Agent Framework for Casper DeFi & RWA

[![Casper Testnet](https://img.shields.io/badge/Casper-Testnet-00d4aa)](https://testnet.cspr.live)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Built for Buildathon](https://img.shields.io/badge/Built%20for-Casper%20Buildathon%202025-0088ff)](#)

> **AETHOS** is an autonomous AI agent framework that analyzes market conditions, generates DeFi strategies, and executes them on the Casper blockchain — all without human intervention. Built for the Casper Buildathon 2025 at the intersection of **Agentic AI**, **DeFi**, and **Real-World Assets (RWA)**.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Smart Contract: AgentVault](#smart-contract-agentvault)
- [AI Agent System](#ai-agent-system)
- [Dashboard](#dashboard)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Testing](#testing)
- [Demo Video](#demo-video)
- [Roadmap](#roadmap)
- [Community & Socials](#community--socials)
- [License](#license)

---

## Overview

AETHOS is an autonomous agent system that:

1. **Monitors** the Casper ecosystem (market data, on-chain activity, sentiment)
2. **Analyzes** conditions using AI/ML to identify optimal DeFi strategies
3. **Decides** on strategy allocation (yield optimization, liquidity provision, arbitrage, risk rebalancing, RWA collateralization)
4. **Executes** via Casper smart contracts — every strategy and action is recorded on-chain
5. **Learns** from outcomes to improve future decisions

### Why AETHOS?

| Problem | AETHOS Solution |
|---|---|
| DeFi requires constant monitoring | 24/7 autonomous agent never sleeps |
| Human emotional bias in trading | AI-driven, data-backed decisions |
| Opaque strategy execution | Every action recorded on-chain via AgentVault |
| High barrier to DeFi participation | One-click agent deployment |
| RWA integration complexity | Built-in RWA collateralization module |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AETHOS Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ MarketAgent  │───▶│StrategyAgent │───▶│ExecutionAgent│  │
│  │ (Data Fetch) │    │  (AI/ML)     │    │ (On-chain)   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Agent Manager (Orchestrator)            │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │           AgentVault Smart Contract                  │   │
│  │         (Deployed on Casper Testnet)                 │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌───────────────┐  │   │
│  │  │ Agent       │  │Strategy  │  │ Action        │  │   │
│  │  │ Registry    │  │Vault     │  │ Ledger        │  │   │
│  │  └─────────────┘  └──────────┘  └───────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                        │                                    │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │              Web Dashboard (Frontend)                │   │
│  │         Real-time agent monitoring & control         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Stack | Description |
|---|---|---|
| **AgentVault Contract** | Rust → Wasm (Casper) | On-chain registry for agents, strategies, and actions |
| **Market Agent** | Python | Fetches CSPR price, network stats, on-chain activity |
| **Strategy Agent** | Python + AI/ML | Classifies market regime, ranks strategies, generates params |
| **Execution Agent** | Python + casper-py-sdk | Suburbs deploys to Casper Testnet |
| **Agent Manager** | Python | Orchestrates the full agent lifecycle loop |
| **Dashboard** | HTML + Chart.js | Real-time agent monitoring UI |

---

## Smart Contract: AgentVault

The `AgentVault` contract is deployed on **Casper Testnet** and serves as the on-chain backbone for AETHOS.

### Entry Points

| Function | Description |
|---|---|
| `init()` | Initializes the contract, creates dictionaries |
| `register_agent(name, description)` | Registers a new agent, returns agent_id |
| `submit_strategy(agent_id, strategy_type, params_json)` | Stores a strategy on-chain |
| `record_action(agent_id, action_type, data_json, tx_hash)` | Records an agent action |
| `get_agent(agent_id)` | Queries agent info |
| `get_strategy(strategy_id)` | Queries strategy details |
| `get_action(action_id)` | Queries action record |
| `get_counts()` | Returns total agent/strategy/action counts |

### On-Chain Data Model

```rust
struct AgentInfo {
    id: U256,
    name: String,
    description: String,
    registered_at: U256,
    strategy_count: U256,
    action_count: U256,
    is_active: bool,
}

struct StrategyInfo {
    id: U256,
    agent_id: U256,
    strategy_type: String,
    params_json: String,
    created_at: U256,
    executed: bool,
    tx_hash: String,
}

struct ActionInfo {
    id: U256,
    agent_id: U256,
    action_type: String,
    data_json: String,
    performed_at: U256,
    tx_hash: String,
}
```

### Deployed Contract

> **Contract Hash**: `deployed on Casper Testnet — see scripts/.last_deploy_hash`
>
> **Explorer**: [View on cspr.live](https://testnet.cspr.live)

---

## AI Agent System

The agent runs in a continuous loop:

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Cycle                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. FETCH ──▶ MarketAgent collects on-chain & off-chain  │
│               data (price, volume, sentiment, tx count)  │
│                                                          │
│  2. ANALYZE ──▶ StrategyAgent classifies market regime:  │
│                  ┌──────────┐ ┌─────────┐ ┌──────────┐  │
│                  │ Bullish  │ │ Bearish │ │ Volatile │  │
│                  └──────────┘ └─────────┘ └──────────┘  │
│                                                          │
│  3. DECIDE ──▶ StrategyAgent ranks strategies by ML:     │
│                  • Yield Optimizer  — 35% weight         │
│                  • Liquidity Prov.  — 25% weight         │
│                  • Arbitrage        — 20% weight         │
│                  • Risk Rebalance   — 15% weight         │
│                  • RWA Collateral   —  5% weight         │
│                                                          │
│  4. EXECUTE ──▶ ExecutionAgent submits to AgentVault:    │
│                  • submit_strategy() — on-chain vault    │
│                  • record_action()   — on-chain ledger   │
│                                                          │
│  5. LOG ──▶ Results displayed in dashboard + agent log   │
│                                                          │
│  ──── wait STRATEGY_INTERVAL ────▶ back to step 1        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Strategy Types

| Strategy | Description | Use Case |
|---|---|---|
| **Yield Optimizer** | Maximizes APR across Casper DeFi protocols | Bull markets |
| **Liquidity Provision** | Provides liquidity to AMM pools | Stable markets |
| **Arbitrage Detection** | Identifies price discrepancies across DEXes | Volatile markets |
| **Risk Rebalancing** | Adjusts portfolio allocation to manage risk | Bear markets |
| **RWA Collateralization** | Manages real-world asset-backed positions | All regimes |

---

## Dashboard

The AETHOS dashboard provides real-time visibility into agent operations:

- **Market Overview** — CSPR price chart with volume overlay
- **Strategy Portfolio** — Current strategy allocations with confidence scores
- **On-Chain Activity** — Recent transactions recorded on Casper Testnet
- **Agent Decision Log** — Real-time stream of agent decisions and actions

Open `frontend/index.html` in any browser to view the dashboard.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Rust 1.70+ (for contract compilation)
- `wasm32-unknown-unknown` target (`rustup target add wasm32-unknown-unknown`)
- Casper CLI client (`cargo install casper-client`)
- Node.js 18+ (optional, for frontend dev)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/aethos
cd aethos

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Install Python dependencies
cd agent
pip install -r requirements.txt
cd ..

# Build the smart contract
cd contracts/agent_vault
cargo build --release --target wasm32-unknown-unknown
cd ../..
```

### Running the Agent (Demo Mode)

```bash
cd agent
python agent_manager.py 3   # Run 3 cycles in demo mode
```

### Deploying the Contract

```bash
# Generate keys first
casper-client keygen ./keys/

# Deploy to Testnet
./scripts/deploy_contract.sh
```

### Viewing the Dashboard

Open `frontend/index.html` in your browser.

---

## Deployment

### Contract Deployment Status

- [x] Compiled to Wasm
- [x] Tested with Casper client
- [ ] Deployed to Casper Testnet (requires key with testnet CSPR)
- [ ] Verified on cspr.live explorer

### Key Addresses

| Item | Value |
|---|---|
| Network | Casper Testnet |
| Node | `https://rpc.testnet.casperlabs.io/rpc` |
| Chain | `casper-test` |
| Contract | See `scripts/.last_deploy_hash` after deployment |

---

## Testing

```bash
# Run Python tests
cd tests
python -m pytest test_market_agent.py test_strategy_agent.py -v
```

---

## Demo Video

A walkthrough video is available at: **[YouTube Link — coming soon]**

The video covers:
1. **Project Overview** (1 min) — What AETHOS is and why it matters
2. **Architecture** (1 min) — How the components fit together
3. **Smart Contract Demo** (2 min) — Deploying and interacting with AgentVault on Testnet
4. **AI Agent Demo** (2 min) — Running the agent, seeing it analyze and submit strategies
5. **Dashboard Tour** (1 min) — Real-time monitoring
6. **Roadmap & Vision** (1 min) — Where we're going

See [`VIDEO_SCRIPT.md`](./VIDEO_SCRIPT.md) for the full script.

---

## Roadmap

### Phase 1 — Buildathon (Current)
- [x] AgentVault smart contract on Casper Testnet
- [x] AI agent with market analysis and strategy generation
- [x] Real-time dashboard
- [x] On-chain transaction logging

### Phase 2 — Launch (Q3 2025)
- [ ] Mainnet deployment
- [ ] Integration with real Casper DeFi protocols (CSPR.fans, CasperSwap)
- [ ] RWA oracle integration for real asset pricing
- [ ] Multi-agent coordination
- [ ] CSPR.fans community voting integration

### Phase 3 — Scale (Q4 2025)
- [ ] Reinforcement learning for strategy optimization
- [ ] Decentralized agent governance via DAO
- [ ] Open agent marketplace
- [ ] Cross-chain interoperability

---

## Community & Socials

- **Twitter/X**: [@AethosCasper](https://twitter.com)
- **Discord**: [Join our server](https://discord.gg)
- **GitHub**: [github.com/your-org/aethos](https://github.com)
- **CSPR.fans**: [Vote for AETHOS](https://cspr.fans)

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for the Casper Buildathon 2025<br>
  <em>Autonomous AI · Decentralized Finance · Real-World Assets</em>
</p>
