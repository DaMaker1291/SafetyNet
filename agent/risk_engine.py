"""Risk Engine — Multi-layer risk management module.

Implements:
  1. Slippage & Impermanent Loss Simulation
  2. Contract Verification (whitelist only)
  3. Rate Limiting & Circuit Breakers
  4. Stress Testing (if-then scenarios)
  5. Position sizing based on risk score

This is the key differentiator — Capital Preservation first.
"""

import json
import time
import math
import hashlib
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any

log = logging.getLogger("safetynet.risk_engine")


class RiskLevel(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class CircuitState(str, Enum):
    CLOSED = "closed"
    TRIPPED = "tripped"
    HALF_OPEN = "half_open"


@dataclass
class RiskScore:
    overall: float
    level: RiskLevel
    slippage_risk: float
    il_risk: float
    contract_risk: float
    concentration_risk: float
    volatility_risk: float
    gas_efficiency: float
    breakdown: dict
    recommendation: str


@dataclass
class StressTestResult:
    scenario: str
    pnl_impact_pct: float
    would_liquidate: bool
    remaining_cushion_pct: float
    recommended_action: str


class RiskEngine:
    """Multi-layer risk management engine.

    Every transaction must pass through this engine before execution.
    """

    def __init__(self):
        self._whitelist: set[str] = set()
        self._circuit_state: dict[str, CircuitState] = {}
        self._tx_history: list[dict] = []
        self._rate_limits: dict[str, float] = {}
        self._max_tx_per_minute = 5
        self._max_volume_per_hour = 50_000.0
        self._hourly_volume = 0.0
        self._volume_reset_time = time.time()

        self._seed_whitelist()

    def _seed_whitelist(self):
        safe = [
            "cspr-usdc", "cspr-eth", "usdc-stcspr",
            "cspr-market", "usdc-market",
            "validator_abc", "validator_def",
        ]
        for addr in safe:
            self.add_to_whitelist(addr)

    def add_to_whitelist(self, address: str):
        self._whitelist.add(address.lower())

    def is_whitelisted(self, address: str) -> bool:
        return address.lower() in self._whitelist

    # --- Slippage & IL Simulation ---

    def simulate_slippage(self, pool_reserve_0: float, pool_reserve_1: float,
                          amount_in: float, is_token0: bool = True) -> dict:
        """Calculate expected slippage for a swap using constant product AMM math."""
        if is_token0:
            k = pool_reserve_0 * pool_reserve_1
            new_reserve_0 = pool_reserve_0 + amount_in
            new_reserve_1 = k / new_reserve_0
            amount_out = pool_reserve_1 - new_reserve_1
        else:
            k = pool_reserve_0 * pool_reserve_1
            new_reserve_1 = pool_reserve_1 + amount_in
            new_reserve_0 = k / new_reserve_1
            amount_out = pool_reserve_0 - new_reserve_0

        price_before = pool_reserve_1 / pool_reserve_0 if is_token0 else pool_reserve_0 / pool_reserve_1
        price_after = new_reserve_1 / new_reserve_0 if is_token0 else new_reserve_0 / new_reserve_1
        slippage_pct = abs(price_after - price_before) / price_before * 100

        return {
            "amount_in": amount_in,
            "amount_out": round(amount_out, 6),
            "price_before": round(price_before, 8),
            "price_after": round(price_after, 8),
            "slippage_pct": round(slippage_pct, 4),
            "price_impact_pct": round(abs(amount_in / (pool_reserve_0 if is_token0 else pool_reserve_1)) * 100, 4),
        }

    def simulate_impermanent_loss(self, price_change_pct: float) -> dict:
        """Calculate IL for a given price change."""
        k = price_change_pct / 100 + 1
        il_pct = (2 * math.sqrt(k) / (1 + k) - 1) * 100
        return {
            "price_change_pct": price_change_pct,
            "impermanent_loss_pct": round(il_pct, 4),
            "break_even_fees_pct": round(abs(il_pct), 4),
        }

    # --- Contract Verification ---

    def verify_contract(self, contract_address: str) -> dict:
        addr = contract_address.lower()
        if addr in self._whitelist:
            return {"verified": True, "address": addr, "audit_status": "pre-audited", "trust_level": "high"}
        return {"verified": False, "address": addr, "audit_status": "unknown", "trust_level": "low"}

    # --- Rate Limiting & Circuit Breakers ---

    def check_rate_limit(self, agent_id: str) -> dict:
        now = time.time()
        minute_ago = now - 60

        recent = [t for t in self._tx_history
                  if t["agent_id"] == agent_id and t["timestamp"] > minute_ago]
        recent_count = len(recent)

        if now - self._volume_reset_time > 3600:
            self._hourly_volume = 0.0
            self._volume_reset_time = now

        return {
            "allowed": recent_count < self._max_tx_per_minute,
            "txs_last_minute": recent_count,
            "max_per_minute": self._max_tx_per_minute,
            "hourly_volume": self._hourly_volume,
            "max_hourly_volume": self._max_volume_per_hour,
        }

    def check_circuit_breaker(self, market: str) -> CircuitState:
        state = self._circuit_state.get(market, CircuitState.CLOSED)
        if state == CircuitState.TRIPPED:
            time_since_trip = time.time() - self._circuit_state.get(f"{market}_tripped_at", 0)
            if time_since_trip > 300:
                self._circuit_state[market] = CircuitState.HALF_OPEN
                return CircuitState.HALF_OPEN
        return state

    def trip_circuit_breaker(self, market: str, reason: str):
        self._circuit_state[market] = CircuitState.TRIPPED
        self._circuit_state[f"{market}_tripped_at"] = time.time()
        log.warning("Circuit breaker TRIPPED for %s: %s", market, reason)

    # --- Stress Testing ---

    def run_stress_test(self, position: dict) -> list[StressTestResult]:
        """Run if-then scenarios on a position."""
        scenarios = [
            {"name": "Asset drops 10%", "drop": -10},
            {"name": "Asset drops 30%", "drop": -30},
            {"name": "Asset drops 50%", "drop": -50},
            {"name": "Asset pumps 20%", "drop": 20},
            {"name": "Volatility spike 3x", "drop": -15},
        ]
        results = []
        entry_price = position.get("entry_price", 0.042)
        position_size = position.get("size", 1000)
        leverage = position.get("leverage", 1)
        liquidation_price = position.get("liquidation_price", 0.0)

        for sc in scenarios:
            new_price = entry_price * (1 + sc["drop"] / 100)
            pnl = (new_price - entry_price) / entry_price * position_size * leverage
            pnl_pct = (new_price - entry_price) / entry_price * 100 * leverage
            would_liquidate = liquidation_price > 0 and new_price <= liquidation_price

            if would_liquidate:
                cushion = 0.0
                action = "LIQUIDATE POSITION — stop loss triggered"
            elif pnl_pct < -20:
                cushion = (new_price - liquidation_price) / new_price * 100 if liquidation_price > 0 else 0
                action = "Reduce position size or hedge"
            elif pnl_pct < -10:
                cushion = (new_price - liquidation_price) / new_price * 100 if liquidation_price > 0 else 25
                action = "Monitor closely, consider partial exit"
            else:
                cushion = 50.0
                action = "Hold — within acceptable range"

            results.append(StressTestResult(
                scenario=sc["name"],
                pnl_impact_pct=round(pnl_pct, 2),
                would_liquidate=would_liquidate,
                remaining_cushion_pct=round(max(0, cushion), 1),
                recommended_action=action,
            ))

        return results

    # --- Comprehensive Risk Assessment ---

    def assess(self, opportunity: dict, position: dict | None = None) -> RiskScore:
        """Run full risk assessment on a yield opportunity."""
        score = 0.0
        breakdown = {}

        # Slippage risk
        slippage = opportunity.get("slippage_pct", 0.5)
        slippage_risk = min(1.0, slippage / 2.0)
        breakdown["slippage"] = {"value": slippage, "risk": slippage_risk}

        # IL risk
        il = opportunity.get("il_risk_pct", 2.0)
        il_risk = min(1.0, il / 20.0)
        breakdown["impermanent_loss"] = {"value": il, "risk": il_risk}

        # Contract risk
        pool_id = opportunity.get("id", "")
        contract_risk = 0.0 if self.is_whitelisted(pool_id) else 0.8
        breakdown["contract"] = {"value": pool_id, "risk": contract_risk}

        # Concentration risk
        position_size = opportunity.get("size", 1000)
        tvl = opportunity.get("tvl", 1_000_000)
        concentration = position_size / tvl if tvl > 0 else 0
        concentration_risk = min(1.0, concentration * 10)
        breakdown["concentration"] = {"value": concentration, "risk": concentration_risk}

        # Volatility risk
        vol = opportunity.get("volatility_pct", 3.0)
        volatility_risk = min(1.0, vol / 15.0)
        breakdown["volatility"] = {"value": vol, "risk": volatility_risk}

        # Gas efficiency
        gas = opportunity.get("gas_cost_usd", 0.5)
        expected_return = opportunity.get("risk_adjusted_apr", 10.0)
        gas_efficiency = min(1.0, (expected_return / 100) / (gas + 0.01))
        breakdown["gas_efficiency"] = {"value": gas, "risk": 1 - gas_efficiency}

        # Weighted overall score
        weights = {
            "slippage": 0.15, "impermanent_loss": 0.20,
            "contract": 0.25, "concentration": 0.10,
            "volatility": 0.15, "gas_efficiency": 0.15,
        }
        overall = sum(
            weights[k] * breakdown[k]["risk"]
            for k in weights
        )

        level = (
            RiskLevel.SAFE if overall < 0.2 else
            RiskLevel.CAUTION if overall < 0.35 else
            RiskLevel.ELEVATED if overall < 0.5 else
            RiskLevel.HIGH if overall < 0.7 else
            RiskLevel.CRITICAL
        )

        recommendation = (
            "EXECUTE — optimal risk-adjusted opportunity"
            if level in (RiskLevel.SAFE, RiskLevel.CAUTION)
            else "CAUTION — consider reducing position size or waiting"
            if level == RiskLevel.ELEVATED
            else "AVOID — risk exceeds threshold, rotate to stable assets"
        )

        return RiskScore(
            overall=round(overall, 4),
            level=level,
            slippage_risk=slippage_risk,
            il_risk=il_risk,
            contract_risk=contract_risk,
            concentration_risk=concentration_risk,
            volatility_risk=volatility_risk,
            gas_efficiency=gas_efficiency,
            breakdown=breakdown,
            recommendation=recommendation,
        )

    def record_transaction(self, agent_id: str, tx_hash: str,
                           volume: float, market: str):
        self._tx_history.append({
            "agent_id": agent_id,
            "tx_hash": tx_hash,
            "volume": volume,
            "market": market,
            "timestamp": time.time(),
        })
        self._hourly_volume += volume
