"""SafetyNet API Server — interactive agent testing via HTTP.

Run with:
    python api_server.py

Then open http://localhost:5000 in your browser.
"""

import json
import sys
import os
import time
import threading
import logging
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request
from flask_cors import CORS

from market_agent import MarketAgent
from strategy_agent import StrategyAgent
from execution_agent import ExecutionAgent

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("safetynet")

# Global agent state
market = MarketAgent()
strategist = StrategyAgent()
executor = ExecutionAgent()
cycle_count = 0
agent_running = False
log_history = []
strategy_history = []


def add_log(level: str, msg: str):
    entry = {"level": level, "msg": msg, "time": time.strftime("%H:%M:%S")}
    log_history.append(entry)
    print(f"[{entry['time']}] {level}: {msg}")


@app.route("/api/status")
def status():
    return jsonify({
        "running": agent_running,
        "cycles": cycle_count,
        "strategies": len(strategy_history),
        "log_count": len(log_history),
    })


@app.route("/api/market")
def market_data():
    snapshot = market.get_snapshot(force=True)
    return jsonify({
        "cspr_price_usd": snapshot.cspr_price_usd,
        "sentiment": snapshot.sentiment_score,
        "tx_count": snapshot.recent_tx_count,
        "peers": snapshot.total_contracts,
        "timestamp": snapshot.timestamp,
    })


@app.route("/api/cycle", methods=["POST"])
def run_cycle():
    global cycle_count
    try:
        body = request.get_json(silent=True) or {}
        agent_id = body.get("agent_id", 1)

        add_log("INFO", "Fetching market data...")
        snapshot = market.get_snapshot(force=True)
        add_log("INFO", f"CSPR ${snapshot.cspr_price_usd:.4f} | Sentiment {snapshot.sentiment_score:.0%}")

        add_log("INFO", "Running AI strategy inference...")
        analysis = strategist.analyze_market(snapshot)
        strategy = strategist.generate_strategy(analysis)
        add_log("INFO", f"Recommended: {strategy['type']} ({strategy['confidence']:.1%})")

        add_log("INFO", "Submitting strategy to AgentVault contract...")
        tx = executor.submit_strategy(agent_id, strategy["type"], json.dumps(strategy["params"]))
        add_log("INFO", f"Strategy submitted — tx: {tx[:16]}...")

        action_tx = executor.record_action(
            agent_id, "strategy_execution",
            json.dumps({"strategy_id": strategy["id"], "type": strategy["type"]}),
            tx,
        )
        add_log("INFO", f"Action recorded — tx: {action_tx[:16]}...")

        cycle_count += 1
        result = {
            "cycle": cycle_count,
            "strategy": strategy["type"],
            "confidence": strategy["confidence"],
            "regime": analysis["market_regime"],
            "tx_hash": tx,
            "status": "submitted",
        }
        strategy_history.append(result)

        return jsonify({"success": True, "result": result})

    except Exception as e:
        add_log("ERROR", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cycles", methods=["POST"])
def run_multiple_cycles():
    body = request.get_json(silent=True) or {}
    n = int(body.get("count", 5))
    delay = float(body.get("delay", 1.0))

    def _run():
        global cycle_count, agent_running
        for i in range(n):
            if not agent_running:
                break
            with app.app_context():
                try:
                    snapshot = market.get_snapshot(force=True)
                    analysis = strategist.analyze_market(snapshot)
                    strategy = strategist.generate_strategy(analysis)
                    tx = executor.submit_strategy(1, strategy["type"], json.dumps(strategy["params"]))
                    action_tx = executor.record_action(1, "strategy_execution", json.dumps({"strategy_id": strategy["id"]}), tx)
                    cycle_count += 1
                    result = {"cycle": cycle_count, "strategy": strategy["type"], "confidence": strategy["confidence"], "regime": analysis["market_regime"]}
                    strategy_history.append(result)
                    add_log("INFO", f"[{i+1}/{n}] {strategy['type']} ({strategy['confidence']:.1%})")
                except Exception as e:
                    add_log("ERROR", str(e))
                time.sleep(delay)
        agent_running = False
        add_log("INFO", f"Completed {n} cycles — agent idle")

    global agent_running
    if agent_running:
        return jsonify({"success": False, "error": "Already running"}), 400

    agent_running = True
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({"success": True, "message": f"Running {n} cycles..."})


@app.route("/api/stop", methods=["POST"])
def stop_agent():
    global agent_running
    agent_running = False
    add_log("INFO", "Agent stopped by user")
    return jsonify({"success": True})


@app.route("/api/logs")
def get_logs():
    since = request.args.get("since", 0, type=int)
    return jsonify(log_history[since:])


@app.route("/api/strategies")
def get_strategies():
    return jsonify(strategy_history)


@app.route("/api/config", methods=["GET", "POST"])
def config():
    global strategist
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        weights = body.get("weights")
        if weights and isinstance(weights, dict):
            from strategy_agent import STRATEGY_WEIGHTS
            for k, v in weights.items():
                if k in STRATEGY_WEIGHTS:
                    STRATEGY_WEIGHTS[k]["weight"] = float(v)
            add_log("INFO", f"Strategy weights updated: {weights}")
        return jsonify({"success": True})
    from strategy_agent import STRATEGY_WEIGHTS
    return jsonify({k: v["weight"] for k, v in STRATEGY_WEIGHTS.items()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"SafetyNet API running on http://localhost:{port}")
    print(f"Open frontend/index.html in your browser and set API URL to http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
