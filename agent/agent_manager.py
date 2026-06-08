#!/usr/bin/env python3
"""AETHOS Agent Manager — orchestrates the full AI agent loop.

The agent:
  1. Fetches market data (MarketAgent)
  2. Analyzes & generates strategies (StrategyAgent)
  3. Submits strategies on-chain (ExecutionAgent)
  4. Records actions on-chain
  5. Logs and waits for next cycle
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from market_agent import MarketAgent
from strategy_agent import StrategyAgent
from execution_agent import ExecutionAgent
from config import (
    CASPER_NODE_URL,
    CHAIN_NAME,
    CONTRACT_HASH,
    CONTRACT_PACKAGE,
    AGENT_SECRET_KEY_PATH,
    AGENT_PUBLIC_KEY_HEX,
    AGENT_NAME,
    AGENT_DESCRIPTION,
    STRATEGY_INTERVAL_SECONDS,
    LOG_LEVEL,
)

console = Console()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("aethos")


class AgentManager:
    """Orchestrates the autonomous agent lifecycle."""

    def __init__(self):
        self.market = MarketAgent(node_url=CASPER_NODE_URL)
        self.strategist = StrategyAgent()
        self.executor = ExecutionAgent(
            node_url=CASPER_NODE_URL,
            chain_name=CHAIN_NAME,
            contract_hash=CONTRACT_HASH,
            contract_package=CONTRACT_PACKAGE,
            secret_key_path=AGENT_SECRET_KEY_PATH,
            public_key_hex=AGENT_PUBLIC_KEY_HEX,
        )
        self.agent_id: int | None = None
        self.cycle_count = 0
        self.running = False

    def initialize(self) -> bool:
        """Register the agent on-chain if not already registered."""
        console.print(Panel.fit(
            "[bold cyan]AETHOS Agent v1.0[/bold cyan]\n"
            "[dim]Autonomous DeFi Agent for Casper Network[/dim]"
        ))

        log.info("Registering agent on Casper Testnet...")
        try:
            deploy_hash = self.executor.register_agent(
                AGENT_NAME, AGENT_DESCRIPTION
            )
            log.info("Agent registered — deploy hash: %s", deploy_hash)
            self.agent_id = 1
            return True
        except Exception as e:
            log.warning("On-chain registration failed (this is OK for demo): %s", e)
            self.agent_id = 1
            return True

    def cycle(self) -> dict:
        """Execute one full agent cycle."""
        self.cycle_count += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        console.rule(f"[bold]Cycle #{self.cycle_count}[/bold] — {timestamp}")

        # Step 1: Gather market data
        log.info("Fetching market data...")
        snapshot = self.market.get_snapshot(force=True)
        console.print(f"  CSPR Price: ${snapshot.cspr_price_usd:.4f}")
        console.print(f"  Sentiment:  {snapshot.sentiment_score:.2%}")
        console.print(f"  TX Volume:  {snapshot.recent_tx_count} txs")

        # Step 2: Analyze and generate strategy
        log.info("Running AI strategy inference...")
        analysis = self.strategist.analyze_market(snapshot)
        strategy = self.strategist.generate_strategy(analysis)

        console.print(Panel(
            f"[bold green]Recommended Strategy:[/bold green] "
            f"{strategy['type'].replace('_', ' ').title()}\n"
            f"  Confidence: {strategy['confidence']:.1%}\n"
            f"  Regime:     {strategy['market_regime'].title()}",
            title="Strategy Decision"
        ))

        # Step 3: Submit to on-chain vault
        log.info("Submitting strategy to AgentVault contract...")
        try:
            tx_hash = self.executor.submit_strategy(
                agent_id=self.agent_id,
                strategy_type=strategy["type"],
                params_json=json.dumps(strategy["params"]),
            )
            log.info("Strategy submitted — deploy hash: %s", tx_hash)

            action_tx = self.executor.record_action(
                agent_id=self.agent_id,
                action_type="strategy_execution",
                data_json=json.dumps({
                    "strategy_id": strategy["id"],
                    "type": strategy["type"],
                    "confidence": strategy["confidence"],
                }),
                tx_hash=tx_hash,
            )
            log.info("Action recorded — deploy hash: %s", action_tx)

            result = {
                "cycle": self.cycle_count,
                "timestamp": timestamp,
                "strategy": strategy,
                "chain_tx": tx_hash,
                "action_tx": action_tx,
                "status": "submitted",
            }
        except Exception as e:
            log.warning("On-chain submission skipped: %s", e)
            result = {
                "cycle": self.cycle_count,
                "timestamp": timestamp,
                "strategy": strategy,
                "chain_tx": "",
                "action_tx": "",
                "status": "simulated",
            }

        # Step 4: Display summary
        table = Table(title=f"Cycle #{self.cycle_count} Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Strategy", strategy["type"])
        table.add_row("Confidence", f"{strategy['confidence']:.1%}")
        table.add_row("Market Regime", strategy["market_regime"].title())
        table.add_row("CSPR Price", f"${snapshot.cspr_price_usd:.4f}")
        table.add_row("Status", result["status"].upper())
        console.print(table)

        return result

    def run(self, cycles: int = 0):
        """Run the agent loop indefinitely or for N cycles."""
        self.running = True

        if not self.initialize():
            log.error("Agent initialization failed")
            return

        log.info("Agent running with %ds interval", STRATEGY_INTERVAL_SECONDS)

        try:
            while self.running:
                self.cycle()
                if cycles and self.cycle_count >= cycles:
                    log.info("Completed %d cycles — shutting down", cycles)
                    break
                log.info("Sleeping %d seconds...", STRATEGY_INTERVAL_SECONDS)
                time.sleep(STRATEGY_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            log.info("Agent stopped by user")
        finally:
            self.running = False

    def stop(self):
        self.running = False


if __name__ == "__main__":
    manager = AgentManager()
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    manager.run(cycles=cycles)
