#!/usr/bin/env bash
# ============================================================
# SafetyNet — AgentVault Session Deploy Script
# Deploys AgentVault session contract to Casper Testnet
# Usage: ./deploy_contract.sh init|register_agent [agent_name agent_data]
# ============================================================
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <method> [args...]"
    echo "  init              — Initialize storage (dict, counters)"
    echo "  register_agent    — Register an agent (needs agent_name agent_data)"
    exit 1
fi

METHOD="$1"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTRACT_DIR="$PROJECT_DIR/contracts/agent_vault"

# ---------- Configuration ----------
CSPR_CLOUD_TOKEN="${CSPR_CLOUD_TOKEN:-019ea917-7049-7319-aa18-a8110aa3952f}"
PROXY_PORT=17777
NODE_ADDRESS="${NODE_ADDRESS:-http://127.0.0.1:$PROXY_PORT}"
NETWORK_NAME="${NETWORK_NAME:-casper-test}"
PAYMENT_AMOUNT="${PAYMENT_AMOUNT:-1000000000}"  # 1 CSPR
TTL="${TTL:-1hour}"

KEY_PATH="${KEY_PATH:-$PROJECT_DIR/keys/secret_key.pem}"
if [ ! -f "$KEY_PATH" ]; then
    echo "ERROR: Secret key not found at $KEY_PATH"
    echo "Generate with: casper-client keygen $PROJECT_DIR/keys/"
    exit 1
fi

# ---------- Build Contract ----------
echo "=============================================="
echo " SafetyNet — AgentVault Deploy"
echo "=============================================="
echo ""
echo "Method: $METHOD"
cd "$CONTRACT_DIR"

if ! command -v cargo &> /dev/null; then
    echo "ERROR: Rust/Cargo not found. Install from https://rustup.rs"
    exit 1
fi

echo "Building contract..."
cargo build --release --target wasm32-unknown-unknown -q
WASM_PATH="$CONTRACT_DIR/target/wasm32-unknown-unknown/release/agent_vault.wasm"

if [ ! -f "$WASM_PATH" ]; then
    echo "ERROR: Build failed — wasm not found at $WASM_PATH"
    exit 1
fi

WASM_SIZE=$(stat -f%z "$WASM_PATH" 2>/dev/null || stat -c%s "$WASM_PATH" 2>/dev/null)
echo "  Compiled: agent_vault.wasm ($(( WASM_SIZE / 1024 )) KB)"

# ---------- Start CSPR.cloud Proxy ----------
PROXY_PID=""
cleanup() {
    if [ -n "$PROXY_PID" ]; then
        kill "$PROXY_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "Starting CSPR.cloud auth proxy on 127.0.0.1:$PROXY_PORT..."
export CSPR_CLOUD_TOKEN
python3 "$SCRIPT_DIR/cspr_cloud_proxy.py" "$PROXY_PORT" &
PROXY_PID=$!
sleep 2

# ---------- Deploy ----------
echo ""
echo "Deploying to Casper Testnet..."
echo "  Node:      $NODE_ADDRESS (via CSPR.cloud)"
echo "  Network:   $NETWORK_NAME"
echo "  Payment:   $PAYMENT_AMOUNT Motes"
echo ""

case "$METHOD" in
    init)
        echo "  Args: method='init'"
        RESULT=$(casper-client put-transaction session \
            --node-address "$NODE_ADDRESS" \
            --chain-name "$NETWORK_NAME" \
            --secret-key "$KEY_PATH" \
            --wasm-path "$WASM_PATH" \
            --session-arg "method:string='init'" \
            --payment-amount "$PAYMENT_AMOUNT" \
            --standard-payment "true" \
            --gas-price-tolerance 1 \
            --ttl "$TTL" 2>&1)
        ;;
    register_agent)
        if [ $# -lt 3 ]; then
            echo "ERROR: register_agent requires agent_name and agent_data"
            exit 1
        fi
        AGENT_JSON="{\"name\":\"$2\",\"data\":\"$3\"}"
        echo "  Args: method='register_agent', name='$2'"
        RESULT=$(casper-client put-transaction session \
            --node-address "$NODE_ADDRESS" \
            --chain-name "$NETWORK_NAME" \
            --secret-key "$KEY_PATH" \
            --wasm-path "$WASM_PATH" \
            --session-args-json "[{\"name\":\"method\",\"type\":\"String\",\"value\":\"register_agent\"},{\"name\":\"agent_name\",\"type\":\"String\",\"value\":\"$2\"},{\"name\":\"agent_data\",\"type\":\"String\",\"value\":\"$3\"}]" \
            --payment-amount "$PAYMENT_AMOUNT" \
            --standard-payment "true" \
            --gas-price-tolerance 1 \
            --ttl "$TTL" 2>&1)
        ;;
    *)
        echo "ERROR: Unknown method '$METHOD'"
        exit 1
        ;;
esac

echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"

HASH=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['result']['transaction_hash']['Version1'])" 2>/dev/null || echo "")
if [ -n "$HASH" ]; then
    echo "$HASH" > "$PROJECT_DIR/scripts/.last_transaction_hash"
    echo "  Transaction hash: $HASH"
fi

# ---------- Verify ----------
echo ""
echo "Waiting for finalization..."
sleep 45

echo ""
echo "=== Result ==="
casper-client get-transaction \
    --node-address "$NODE_ADDRESS" \
    "$HASH" 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('result', {})
ei = r.get('execution_info', {})
er = ei.get('execution_result', {}).get('Version2', {})
error = er.get('error_message', '')
print('error:', error if error else 'none')
print('consumed:', er.get('consumed', 'N/A'))
cost = er.get('cost', 'N/A')
if cost != 'N/A':
    csp = int(cost) / 1_000_000_000
    print('cost: {:.9f} CSPR'.format(csp))
if not error:
    print('SUCCESS!')
"
