#!/usr/bin/env bash
# ============================================================
# SafetyNet — AgentVault Contract Deploy Script
# Deploys the AgentVault smart contract to Casper Testnet
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTRACT_DIR="$PROJECT_DIR/contracts/agent_vault"

# ---------- Configuration ----------
NODE_ADDRESS="${NODE_ADDRESS:-https://rpc.testnet.casperlabs.io/rpc}"
NETWORK_NAME="${NETWORK_NAME:-casper-test}"
PAYMENT_AMOUNT="${PAYMENT_AMOUNT:-5000000000}"  # 5 CSPR
TTL="${TTL:-3600000}"  # 1 hour

KEY_PATH="${KEY_PATH:-$PROJECT_DIR/keys/account_key.pem}"
if [ ! -f "$KEY_PATH" ]; then
    echo "ERROR: Secret key not found at $KEY_PATH"
    echo "Generate one with: casper-client keygen $PROJECT_DIR/keys/"
    exit 1
fi

# ---------- Build Contract ----------
echo "=============================================="
echo " SafetyNet — AgentVault Deploy"
echo "=============================================="
echo ""
echo "Building contract..."
cd "$CONTRACT_DIR"

if ! command -v cargo &> /dev/null; then
    echo "ERROR: Rust/Cargo not found. Install from https://rustup.rs"
    exit 1
fi

if ! rustup target list --installed | grep -q wasm32-unknown-unknown; then
    echo "Adding wasm32-unknown-unknown target..."
    rustup target add wasm32-unknown-unknown
fi

cargo build --release --target wasm32-unknown-unknown
WASM_PATH="$CONTRACT_DIR/target/wasm32-unknown-unknown/release/agent_vault.wasm"

if [ ! -f "$WASM_PATH" ]; then
    echo "ERROR: Build failed — wasm not found at $WASM_PATH"
    exit 1
fi

WASM_SIZE=$(stat -f%z "$WASM_PATH" 2>/dev/null || stat -c%s "$WASM_PATH" 2>/dev/null)
echo "  Compiled: agent_vault.wasm ($(( WASM_SIZE / 1024 )) KB)"

# ---------- Deploy ----------
echo ""
echo "Deploying to Casper Testnet..."
echo "  Node:      $NODE_ADDRESS"
echo "  Network:   $NETWORK_NAME"
echo "  Key:       $KEY_PATH"
echo "  Payment:   $PAYMENT_AMOUNT Motes"
echo ""

DEPLOY_HASH=$(casper-client put-deploy \
    --node-address "$NODE_ADDRESS" \
    --chain-name "$NETWORK_NAME" \
    --secret-key "$KEY_PATH" \
    --session-path "$WASM_PATH" \
    --payment-amount "$PAYMENT_AMOUNT" \
    --ttl "$TTL" \
    -q)

echo "Deploy submitted!"
echo "  Deploy Hash: $DEPLOY_HASH"
echo ""
echo "Monitor at: https://testnet.cspr.live/deploy/$DEPLOY_HASH"
echo ""

# Save deploy hash
echo "$DEPLOY_HASH" > "$PROJECT_DIR/scripts/.last_deploy_hash"
echo "Saved to scripts/.last_deploy_hash"

# ---------- Verify ----------
echo ""
echo "Waiting for deployment to finalize..."
sleep 30

casper-client get-deploy \
    --node-address "$NODE_ADDRESS" \
    "$DEPLOY_HASH" \
    | jq '.result.execution_results[0]' \
    > "$PROJECT_DIR/scripts/.deploy_result.json" 2>/dev/null || true

echo "Done! Check .deploy_result.json for execution outcome."
echo ""

# Extract contract hash if deployed successfully
CONTRACT_HASH=$(cat "$PROJECT_DIR/scripts/.deploy_result.json" \
    | grep -o '"contract_hash": "[^"]*"' \
    | cut -d'"' -f4 2>/dev/null || echo "")

if [ -n "$CONTRACT_HASH" ]; then
    echo "Contract Hash: $CONTRACT_HASH"
    echo ""
    echo "Update your .env with:"
    echo "  CONTRACT_HASH=$CONTRACT_HASH"
else
    echo "Contract hash not found in result."
    echo "Check deploy status: casper-client get-deploy --node-address $NODE_ADDRESS $DEPLOY_HASH"
fi
