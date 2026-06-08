#!/usr/bin/env bash
# SafetyNet — Launch the interactive test environment
# Starts the API server and opens the dashboard.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$SCRIPT_DIR/agent"
FRONTEND="$SCRIPT_DIR/frontend/index.html"
PORT="${PORT:-5100}"

echo "=============================================="
echo " SafetyNet — Interactive Test Environment"
echo "=============================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Install deps
echo "Installing dependencies..."
pip3 install -r "$AGENT_DIR/requirements.txt" -q 2>/dev/null || true

echo ""
echo ""
echo "  Dashboard: open frontend/index.html in your browser"
echo "  API:       http://localhost:$PORT/api/"
echo "  To run:    Click 'Run 1 Cycle' or 'Run N cycles'
echo ""
echo "Opening dashboard..."
echo ""

# Open dashboard after a brief delay
(sleep 2 && open "$FRONTEND") &

# Start API server
cd "$AGENT_DIR"
python3 api_server.py
