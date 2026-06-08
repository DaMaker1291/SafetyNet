#!/usr/bin/env bash
# ============================================================
# AETHOS — Test Agent Script
# Runs the AI agent locally in demo mode (3 cycles)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
AGENT_DIR="$PROJECT_DIR/agent"

echo "=============================================="
echo " AETHOS — Agent Test Run"
echo "=============================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found"
    exit 1
fi

# Install deps
echo "Installing agent dependencies..."
cd "$AGENT_DIR"
pip3 install -r requirements.txt -q 2>/dev/null || true

# Run agent (3 cycles, simulated on-chain)
echo ""
echo "Running agent for 3 cycles..."
echo "NOTE: This runs in demo/simulated mode."
echo "      For full on-chain mode, set CONTRACT_HASH in .env"
echo ""

python3 agent_manager.py 3

echo ""
echo "=============================================="
echo " Test complete!"
echo "=============================================="
