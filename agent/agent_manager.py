#!/usr/bin/env python3
"""SafetyNet v2 Agent Manager — orchestrates the full autonomous yield-routing engine.

Architecture:
  Observer (Data Bus) → Strategy Engine (Heuristic Model) → Risk Engine (Guardrails)
    → Transaction Orchestrator (Batching) → MCP Server (Casper Bridge)

Phases:
  Phase 1: Read-only mode with alerts (validate math)
  Phase 2: Paper trading (simulate transactions)
  Phase 3: Limited autonomy (small capital, manual approval)
  Phase 4: Full orchestration (all guardrails active)
"""

import json
import os
import sys
import time
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

from observer import Observer
from strategy_engine import StrategyEngine, RankedOpportunity
from risk_engine import RiskEngine, RiskLevel, CircuitState
from transaction_orchestrator import TransactionOrchestrator, TxPriority
from execution_agent import ExecutionAgent
from mcp_server import MCPServer
from gas_forecaster import GasForecaster
from config import (
    CASPER_NODE_URL, CHAIN_NAME, AGENT_NAME,
    STRATEGY_INTERVAL_SECONDS, LOG_LEVEL,
)

console = Console()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("safetynet")


class SafetyNetAgent:
    """Orchestrates the complete autonomous yield-routing lifecycle."""

    def __init__(self, phase: int = 2):
        self.phase = phase
        self.running = False
        self.cycle_count = 0

        # Core components
        self.observer = Observer(node_url=CASPER_NODE_URL)
        self.strategy_engine = StrategyEngine()
        self.risk_engine = RiskEngine()
        self.gas_forecaster = GasForecaster()
        self.mcp_server = MCPServer(node_url=CASPER_NODE_URL)
        self.executor = ExecutionAgent()  # demo mode
        self.orchestrator = TransactionOrchestrator(gas_forecaster=self.gas_forecaster)

        # Wire executor to orchestrator
        self.orchestrator.set_executor(self._execute_transaction)

        # State
        self.current_allocation: dict | None = None
        self.cycle_history: list[dict] = []
        self.alert_history: list[dict] = []

        log.info("SafetyNet v2 initialized (Phase %d)", phase)
        if phase == 1:
            log.info("  Phase 1: READ-ONLY — alerts only, no transactions")
        elif phase == 2:
            log.info("  Phase 2: PAPER TRADING — simulated transactions")
        elif phase == 3:
            log.info("  Phase 3: LIMITED AUTONOMY — small capital, manual approval")
        elif phase == 4:
            log.info("  Phase 4: FULL ORCHESTRATION — all guardrails active")

    def _execute_transaction(self, tx_type: str, params: dict) -> dict:
        """Execute a single transaction (delegates to ExecutionAgent or simulates)."""
        if self.phase == 1:
            return {"status": "readonly", "tx_hash": "", "note": "Phase 1: no transactions"}
        return {
            "tx_hash": self.executor.submit_strategy(1, tx_type, json.dumps(params)),
            "status": "simulated" if self.phase == 2 else "submitted",
        }

    def cycle(self) -> dict:
        """Execute one full agent cycle."""
        self.cycle_count += 1
        timestamp = datetime.now(timezone.utc).isoformat()
        start_time = time.time()

        console.rule(f"[bold]SafetyNet Cycle #{self.cycle_count}[/bold] — {timestamp}")

        # Step 1: Observe — poll all data sources
        log.info("Polling all Casper data sources...")
        self.observer.poll_all(force=True)
        pools = self.observer.get_all_pools()
        lending = self.observer.get_all_lending_markets()
        volatility = {t: self.observer.get_volatility(t) for t in ["CSPR", "USDC"]}
        congestion = self.observer.get_network_congestion()

        observer_data = {
            "pools": pools,
            "lending_markets": lending,
            "volatility": volatility,
            "congestion": congestion,
        }
        log.info("  %d pools, %d lending markets, congestion=%s",
                 len(pools), len(lending), congestion["level"])

        # Step 2: Evaluate — run strategy engine
        log.info("Running heuristic APR/APY evaluation...")
        opportunities = self.strategy_engine.evaluate_all(observer_data)
        log.info("  Found %d yield opportunities", len(opportunities))

        for opp in opportunities[:3]:
            log.info("  └ %s on %s: %.1f%% net APR (risk=%.3f)",
                     opp.strategy.value, opp.pool_or_market, opp.net_apr, opp.risk_score)

        # Step 3: Select optimal within risk threshold
        selected = self.strategy_engine.select_optimal(opportunities, max_risk=0.35)
        log.info("Selected %d opportunities within risk threshold", len(selected))

        # Step 4: Risk assessment on each selected opportunity
        passed_risk = []
        for opp in selected:
            opp_dict = {
                "id": opp.pool_or_market,
                "slippage_pct": 0.3,
                "il_risk_pct": opp.risk_score * 20,
                "risk_adjusted_apr": opp.net_apr,
                "tvl": 1_000_000,
                "size": 1000,
                "volatility_pct": 3.0,
                "gas_cost_usd": opp.gas_cost_usd,
            }
            risk_score = self.risk_engine.assess(opp_dict)
            opp.risk_score = risk_score.overall

            log.info("  Risk for %s: %s (score=%.3f) — %s",
                     opp.pool_or_market, risk_score.level.value,
                     risk_score.overall, risk_score.recommendation)

            if risk_score.level in (RiskLevel.SAFE, RiskLevel.CAUTION):
                passed_risk.append(opp)
            else:
                log.warning("  ⛔ %s rejected by risk engine: %s",
                            opp.pool_or_market, risk_score.recommendation)

        log.info("  %d/%d passed risk assessment", len(passed_risk), len(selected))

        # Step 5: Generate allocation plan
        if passed_risk:
            self.current_allocation = self.strategy_engine.get_allocation_plan(
                passed_risk, total_capital=10_000.0
            )
        else:
            hold_opp = RankedOpportunity(
                strategy="hold", pool_or_market="stable_reserve",
                gross_apr=0, net_apr=0, risk_score=0,
                gas_cost_usd=0, latency_ms=0, sustainability_score=1,
                confidence=1, reasoning="All opportunities rejected by risk engine — rotating to stable",
            )
            self.current_allocation = {
                "plan": "HOLD — All capital to stable assets",
                "reason": "No acceptable risk-adjusted opportunities",
                "allocations": [{"strategy": "hold", "target": "USDC Reserve",
                                  "allocation_pct": 100, "allocation_usd": 10_000}],
                "timestamp": time.time(),
            }
            passed_risk = [hold_opp]

        # Step 6: Execute via Transaction Orchestrator
        tx_results = []
        for alloc in self.current_allocation.get("allocations", []):
            urgency = "normal" if alloc.get("risk_score", 0) < 0.2 else "high"

            # Check gas forecast
            schedule = self.orchestrator.optimal_schedule(alloc["strategy"], urgency)

            if schedule.get("execute_now", True) or self.phase >= 3:
                tx = self.orchestrator.submit(
                    tx_type=alloc["strategy"],
                    params={"target": alloc["target"], "amount": alloc["allocation_usd"]},
                    priority=TxPriority.HIGH if urgency == "high" else TxPriority.MEDIUM,
                    urgency=urgency,
                )
                tx_results.append(tx.to_dict())

                # Record in risk engine
                self.risk_engine.record_transaction(
                    "safetynet_v2", tx.tx_hash or "",
                    alloc["allocation_usd"], alloc["target"]
                )
            else:
                log.info("  ⏳ Deferring %s: %s", alloc["strategy"], schedule.get("reason", ""))

        # Step 7: Generate summary
        duration = time.time() - start_time
        result = {
            "cycle": self.cycle_count,
            "timestamp": timestamp,
            "duration_seconds": round(duration, 2),
            "opportunities_found": len(opportunities),
            "opportunities_selected": len(selected),
            "passed_risk": len(passed_risk),
            "transactions": tx_results,
            "congestion": congestion["level"],
            "allocation_plan": self.current_allocation,
        }
        self.cycle_history.append(result)

        # Display summary
        self._display_summary(result, opportunities, passed_risk)
        return result

    def _display_summary(self, result: dict, opportunities: list,
                          passed: list):
        table = Table(title=f"Cycle #{result['cycle']} — Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Duration", f"{result['duration_seconds']}s")
        table.add_row("Opportunities Found", str(result['opportunities_found']))
        table.add_row("Passed Risk Assessment", str(result['passed_risk']))
        table.add_row("Network Congestion", result['congestion'].upper())
        if result.get("transactions"):
            table.add_row("TX Submitted", str(len(result["transactions"])))
        console.print(table)

        if self.current_allocation and self.current_allocation.get("allocations"):
            alloc_table = Table(title="Allocation Plan")
            alloc_table.add_column("Strategy", style="yellow")
            alloc_table.add_column("Target", style="cyan")
            alloc_table.add_column("Allocation", style="magenta")
            alloc_table.add_column("Net APR", style="green")
            for a in self.current_allocation["allocations"]:
                alloc_table.add_row(
                    a["strategy"], a["target"],
                    f"{a.get('allocation_pct', 0)}%",
                    f"{a.get('expected_net_apr', 0):.1f}%",
                )
            console.print(alloc_table)

    def run_cycles(self, cycles: int = 1):
        """Run N cycles."""
        self.running = True
        for i in range(cycles):
            if not self.running:
                break
            try:
                self.cycle()
                if i < cycles - 1:
                    log.info("Waiting %d seconds before next cycle...", 5)
                    time.sleep(5)
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error("Cycle %d failed: %s", i + 1, e)
        self.running = False

    def stop(self):
        self.running = False
        log.info("Agent stopped")

    def get_status(self) -> dict:
        return {
            "phase": self.phase,
            "running": self.running,
            "cycles": self.cycle_count,
            "opportunities_evaluated": sum(
                c.get("opportunities_found", 0) for c in self.cycle_history
            ),
            "transactions_submitted": sum(
                len(c.get("transactions", [])) for c in self.cycle_history
            ),
            "queue": self.orchestrator.get_queue_stats(),
        }

    def get_top_opportunities(self, raw: bool = False) -> list:
        self.observer.poll_all(force=True)
        data = {
            "pools": self.observer.get_all_pools(),
            "lending_markets": self.observer.get_all_lending_markets(),
            "volatility": {t: self.observer.get_volatility(t) for t in ["CSPR", "USDC"]},
        }
        opps = self.strategy_engine.evaluate_all(data)
        selected = self.strategy_engine.select_optimal(opps)
        if raw:
            return opps
        return [
            {
                "strategy": o.strategy.value,
                "target": o.pool_or_market,
                "gross_apr": o.gross_apr,
                "net_apr": o.net_apr,
                "risk_score": o.risk_score,
                "gas_cost_usd": o.gas_cost_usd,
                "confidence": o.confidence,
                "reasoning": o.reasoning,
            }
            for o in selected
        ]

    def run_stress_test(self, position: dict | None = None) -> list[dict]:
        if position is None:
            position = {
                "entry_price": 0.042,
                "size": 5000,
                "leverage": 1,
                "liquidation_price": 0.0,
            }
        results = self.risk_engine.run_stress_test(position)
        return [{"scenario": r.scenario, "pnl_pct": r.pnl_impact_pct,
                  "would_liquidate": r.would_liquidate,
                  "cushion_pct": r.remaining_cushion_pct,
                  "action": r.recommended_action} for r in results]


if __name__ == "__main__":
    phase = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    agent = SafetyNetAgent(phase=phase)

    if cycles > 0:
        agent.run_cycles(cycles)
    else:
        agent.run_cycles(1)
