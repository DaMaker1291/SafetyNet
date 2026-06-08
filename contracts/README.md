# AgentVault — Casper Smart Contract

The on-chain registry and execution layer for SafetyNet autonomous agents.

## Build

```bash
cd agent_vault
cargo build --release --target wasm32-unknown-unknown
```

The compiled Wasm will be at:
`agent_vault/target/wasm32-unknown-unknown/release/agent_vault.wasm`

## Deploy

```bash
casper-client put-deploy \
  --node-address https://rpc.testnet.casperlabs.io/rpc \
  --chain-name casper-test \
  --secret-key ./keys/account_key.pem \
  --session-path agent_vault/target/wasm32-unknown-unknown/release/agent_vault.wasm \
  --payment-amount 5000000000
```

## Entry Points

See main README for full documentation of all 8 entry points.

## Dictionaries

Three dictionaries store on-chain state:
- `agents` — keyed by agent_id → AgentInfo
- `strategies` — keyed by strategy_id → StrategyInfo
- `actions` — keyed by action_id → ActionInfo
