"""SafetyNet v2 API Server — exposes the full agent architecture over HTTP.

Run with:
    python api_server.py

Endpoints:
  GET/POST /api/cycle          — Run agent cycles
  GET       /api/opportunities — View top yield opportunities
  GET/POST  /api/risk/assess   — Assess risk for an opportunity
  POST      /api/risk/stress   — Run stress tests on a position
  GET       /api/mcp/tools     — List MCP server tools
  POST      /api/mcp/call      — Call an MCP tool
  GET       /api/gas/forecast  — Gas price forecast
  GET       /api/orchestrator  — Transaction queue stats
  GET       /api/status        — Agent status
  GET/POST  /api/config        — Strategy weights config
"""

import json
import os
import sys
import time
import logging
import threading
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request
from flask_cors import CORS

log = logging.getLogger("safetynet.api")

app = Flask(__name__)
CORS(app)

# Global agent instance
from agent_manager import SafetyNetAgent
agent = SafetyNetAgent(phase=2)

log_history = []
_cycle_thread: threading.Thread | None = None


def add_log(level: str, msg: str, component: str = "api"):
    entry = {"time": time.strftime("%H:%M:%S"), "level": level,
             "msg": msg, "component": component}
    log_history.append(entry)
    print(f"[{entry['time']}] [{component}] {level}: {msg}")


# ─── Agent Control ──────────────────────────────────────────

@app.route("/api/status")
def status():
    s = agent.get_status()
    s["log_count"] = len(log_history)
    return jsonify(s)


@app.route("/api/cycle", methods=["POST"])
def run_one_cycle():
    try:
        result = agent.cycle()
        add_log("INFO", f"Cycle #{result['cycle']} complete — {result['passed_risk']} opportunities passed risk")
        return jsonify({"success": True, "result": result})
    except Exception as e:
        add_log("ERROR", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cycles", methods=["POST"])
def run_multiple():
    global _cycle_thread
    body = request.get_json(silent=True) or {}
    n = int(body.get("count", 3))
    phase = int(body.get("phase", 2))

    if _cycle_thread and _cycle_thread.is_alive():
        return jsonify({"success": False, "error": "Already running"}), 400

    def _run():
        global agent
        agent = SafetyNetAgent(phase=phase)
        add_log("INFO", f"Running {n} cycles (Phase {phase})...")
        agent.run_cycles(n)
        add_log("INFO", f"Completed {n} cycles")

    _cycle_thread = threading.Thread(target=_run, daemon=True)
    _cycle_thread.start()
    return jsonify({"success": True, "message": f"Running {n} cycles (Phase {phase})..."})


@app.route("/api/stop", methods=["POST"])
def stop_agent():
    agent.stop()
    add_log("INFO", "Agent stopped by user")
    return jsonify({"success": True})


# ─── Opportunities ──────────────────────────────────────────

@app.route("/api/opportunities")
def get_opportunities():
    try:
        opps = agent.get_top_opportunities()
        return jsonify({"count": len(opps), "opportunities": opps})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/opportunities/all")
def get_all_opportunities():
    try:
        opps = agent.get_top_opportunities(raw=True)
        results = []
        for o in opps:
            results.append({
                "strategy": o.strategy.value if hasattr(o.strategy, 'value') else str(o.strategy),
                "target": o.pool_or_market,
                "gross_apr": o.gross_apr,
                "net_apr": o.net_apr,
                "risk_score": o.risk_score,
                "gas_cost_usd": o.gas_cost_usd,
                "latency_ms": o.latency_ms,
                "sustainability": o.sustainability_score,
                "confidence": o.confidence,
                "reasoning": o.reasoning,
            })
        return jsonify({"count": len(results), "opportunities": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Risk Engine ────────────────────────────────────────────

@app.route("/api/risk/assess", methods=["POST"])
def assess_risk():
    body = request.get_json(silent=True) or {}
    opp = body.get("opportunity", {})
    position = body.get("position")
    risk_score = agent.risk_engine.assess(opp, position)
    return jsonify({
        "overall": risk_score.overall,
        "level": risk_score.level.value,
        "slippage_risk": risk_score.slippage_risk,
        "il_risk": risk_score.il_risk,
        "contract_risk": risk_score.contract_risk,
        "concentration_risk": risk_score.concentration_risk,
        "volatility_risk": risk_score.volatility_risk,
        "gas_efficiency": risk_score.gas_efficiency,
        "breakdown": risk_score.breakdown,
        "recommendation": risk_score.recommendation,
    })


@app.route("/api/risk/stress", methods=["POST"])
def run_stress():
    body = request.get_json(silent=True) or {}
    position = body.get("position")
    results = agent.run_stress_test(position)
    return jsonify({"scenarios": results})


@app.route("/api/risk/whitelist", methods=["GET", "POST"])
def whitelist():
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        addr = body.get("address", "")
        if addr:
            agent.risk_engine.add_to_whitelist(addr)
            agent.mcp_server.whitelist_contract(addr)
            add_log("INFO", f"Whitelisted: {addr}")
            return jsonify({"success": True, "address": addr})
        return jsonify({"success": False, "error": "No address provided"}), 400
    return jsonify({"whitelist": sorted(agent.risk_engine._whitelist)})


# ─── MCP Server ─────────────────────────────────────────────

@app.route("/api/mcp/tools")
def mcp_tools():
    return jsonify({"tools": agent.mcp_server.list_tools()})


@app.route("/api/mcp/resources")
def mcp_resources():
    return jsonify({"resources": agent.mcp_server.list_resources()})


@app.route("/api/mcp/call", methods=["POST"])
def mcp_call():
    body = request.get_json(silent=True) or {}
    tool = body.get("tool", "")
    args = body.get("arguments", {})
    result = agent.mcp_server.call_tool(tool, args)
    add_log("INFO", f"MCP call: {tool}({json.dumps(args)[:60]})", "mcp")
    return jsonify(result)


# ─── Gas Forecaster ─────────────────────────────────────────

@app.route("/api/gas/forecast")
def gas_forecast():
    windows = agent.gas_forecaster.forecast_windows()
    congestion = agent.gas_forecaster.current_congestion()
    return jsonify({
        "current": congestion,
        "best_windows": [
            {"start_utc": time.strftime("%H:%M UTC", time.gmtime(w.window_start)),
             "end_utc": time.strftime("%H:%M UTC", time.gmtime(w.window_end)),
             "congestion": w.congestion.value,
             "estimated_gas_motes": w.estimated_gas_price_motes,
             "confidence": w.confidence,
             "reason": w.reason}
            for w in windows
        ],
    })


@app.route("/api/gas/schedule", methods=["POST"])
def gas_schedule():
    body = request.get_json(silent=True) or {}
    tx_type = body.get("tx_type", "swap")
    urgency = body.get("urgency", "normal")
    return jsonify(agent.gas_forecaster.optimal_schedule(tx_type, urgency))


# ─── Transaction Orchestrator ───────────────────────────────

@app.route("/api/orchestrator")
def orchestrator_stats():
    return jsonify(agent.orchestrator.get_queue_stats())


@app.route("/api/orchestrator/history")
def tx_history():
    return jsonify({"transactions": agent.orchestrator.get_history()})


@app.route("/api/orchestrator/submit", methods=["POST"])
def submit_tx():
    body = request.get_json(silent=True) or {}
    tx = agent.orchestrator.submit(
        tx_type=body.get("tx_type", "swap"),
        params=body.get("params", {}),
        priority=body.get("priority", 1),
        urgency=body.get("urgency", "normal"),
    )
    add_log("INFO", f"TX submitted: {tx.tx_type} -> {tx.id}", "orchestrator")
    return jsonify(tx.to_dict())


# ─── Observer Data ──────────────────────────────────────────

@app.route("/api/observer/pools")
def observer_pools():
    return jsonify({"pools": agent.observer.get_all_pools()})


@app.route("/api/observer/lending")
def observer_lending():
    return jsonify({"markets": agent.observer.get_all_lending_markets()})


@app.route("/api/observer/congestion")
def observer_congestion():
    return jsonify(agent.observer.get_network_congestion())


# ─── Logs ───────────────────────────────────────────────────

@app.route("/api/logs")
def get_logs():
    since = request.args.get("since", 0, type=int)
    return jsonify(log_history[since:])


# ─── Config ─────────────────────────────────────────────────

@app.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        weights = body.get("weights")
        phase = body.get("phase")
        if weights:
            agent.strategy_engine.update_weights(weights)
            add_log("INFO", f"Strategy weights updated")
        if phase is not None:
            agent.phase = int(phase)
            add_log("INFO", f"Phase changed to {phase}")
        return jsonify({"success": True})
    return jsonify({
        "weights": agent.strategy_engine._weights,
        "phase": agent.phase,
    })


# ─── Market Data ────────────────────────────────────────────

@app.route("/api/market")
def market_data():
    agent.observer.poll_all(force=True)
    pools = agent.observer.get_all_pools()
    congestion = agent.observer.get_network_congestion()
    return jsonify({
        "cspr_price_usd": pools[0].get("price", 0.042) if pools else 0.042,
        "pools_count": len(pools),
        "congestion": congestion["level"],
        "timestamp": time.time(),
    })


# ─── Main ───────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5100))
    add_log("INFO", f"SafetyNet v2 API on http://localhost:{port}")
    print(f"  Dashboard: open frontend/index.html (set port to {port})")
    print(f"  API:       http://localhost:{port}/api/")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
