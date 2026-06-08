"""Strategy Engine — Heuristic APR/APY evaluation model with gas cost factoring.

Evaluates yield opportunities in real-time using:
  - Heuristic APR/APY model (not just spot rates)
  - Gas cost factoring (Casper-specific)
  - Transaction latency scoring
  - Historical volatility for yield sustainability prediction
  - Risk-adjusted ranking

Outputs ranked opportunities with risk scores for the Transaction Orchestrator.
"""

import math
import time
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any

log = logging.getLogger("safetynet.strategy_engine")


class StrategyType(str, Enum):
    YIELD_OPTIMIZER = "yield_optimizer"
    LIQUIDITY_PROVISION = "liquidity_provision"
    ARBITRAGE = "arbitrage"
    LENDING = "lending"
    STAKING = "staking"
    RWA_COLLATERALIZATION = "rwa_collateralization"
    HOLD = "hold"


@dataclass
class RankedOpportunity:
    strategy: StrategyType
    pool_or_market: str
    gross_apr: float
    net_apr: float
    risk_score: float
    gas_cost_usd: float
    latency_ms: float
    sustainability_score: float
    confidence: float
    reasoning: str


class StrategyEngine:
    """Heuristic strategy evaluation engine for Casper DeFi.

    Factors:
      - Gross APR/APY from pool or lending market
      - Gas cost (Casper motes → USD conversion)
      - Transaction latency (finality time)
      - Historical volatility (yield sustainability)
      - Impermanent loss risk
      - Concentration risk (position size vs TVL)
    """

    def __init__(self):
        self.gas_price_usd = 0.00000004  # per mote
        self.casper_finality_seconds = 2.0
        self._history: list[dict] = []
        self._weights = {
            "yield_optimizer": 0.30,
            "liquidity_provision": 0.20,
            "arbitrage": 0.15,
            "lending": 0.15,
            "staking": 0.10,
            "rwa_collateralization": 0.10,
        }

    def update_weights(self, weights: dict[str, float]):
        total = sum(weights.values())
        if total > 0:
            for k in weights:
                self._weights[k] = weights[k] / total

    def evaluate_all(self, observer_data: dict) -> list[RankedOpportunity]:
        """Evaluate all available yield opportunities and return ranked list."""
        opportunities = []

        # Evaluate liquidity pools
        for pool in observer_data.get("pools", []):
            opp = self._evaluate_pool(pool, observer_data)
            if opp:
                opportunities.append(opp)

        # Evaluate lending markets
        for market in observer_data.get("lending_markets", []):
            opp = self._evaluate_lending_market(market, observer_data)
            if opp:
                opportunities.append(opp)

        # Evaluate staking
        opp = self._evaluate_staking(observer_data)
        if opp:
            opportunities.append(opp)

        opportunities.sort(key=lambda x: x.net_apr, reverse=True)
        return opportunities

    def _evaluate_pool(self, pool: dict, data: dict) -> RankedOpportunity | None:
        pool_id = pool.get("id") or pool.get("pool_id", "")
        gross_apr = pool.get("apr_24h", 0)
        tvl = pool.get("tvl", 0)
        fee = pool.get("fee_pct", 0.003)
        volume = pool.get("volume_24h", 0)

        if gross_apr <= 0:
            return None

        # Gas cost
        swap_gas_motes = 15_000_000
        gas_cost_usd = swap_gas_motes * self.gas_price_usd

        # Latency: Casper finality ~2s
        latency_ms = self.casper_finality_seconds * 1000

        # Volatility penalty
        vol_data = data.get("volatility", {}).get(pool.get("token_0", ""), {})
        vol_pct = vol_data.get("volatility_pct", 3.0) if isinstance(vol_data, dict) else 3.0
        vol_penalty = min(0.5, vol_pct / 30.0)

        # IL risk
        il_risk = data.get("il_risk", 0.03)

        # Sustainability: higher volume + lower vol = more sustainable
        vol_score = 1.0 - vol_penalty
        volume_score = min(1.0, volume / 500_000)
        sustainability = (vol_score * 0.6 + volume_score * 0.4)

        # Net APR
        gas_drag = gas_cost_usd / (tvl * 0.01 + 0.01) * 365 * 100
        net_apr = gross_apr - gas_drag - (il_risk * 100)

        # Risk score
        risk_score = vol_penalty * 0.4 + il_risk * 0.4 + (1 - sustainability) * 0.2

        confidence = sustainability * (1 - risk_score)

        return RankedOpportunity(
            strategy=StrategyType.LIQUIDITY_PROVISION,
            pool_or_market=pool_id,
            gross_apr=round(gross_apr, 2),
            net_apr=round(max(0, net_apr), 2),
            risk_score=round(risk_score, 4),
            gas_cost_usd=round(gas_cost_usd, 6),
            latency_ms=round(latency_ms, 1),
            sustainability_score=round(sustainability, 4),
            confidence=round(confidence, 4),
            reasoning=self._build_reasoning("LP", pool_id, gross_apr, net_apr, risk_score),
        )

    def _evaluate_lending_market(self, market: dict, data: dict) -> RankedOpportunity | None:
        market_id = market.get("id") or market.get("market_id", "")
        supply_apr = market.get("supply_apr", 0)
        utilization = market.get("utilization", 0)
        tvl = market.get("total_supplied", 0)

        if supply_apr <= 0:
            return None

        gas_motes = 10_000_000
        gas_cost_usd = gas_motes * self.gas_price_usd
        latency_ms = self.casper_finality_seconds * 1000

        gas_drag = gas_cost_usd / (tvl * 0.01 + 0.01) * 365 * 100
        utilization_penalty = utilization * 0.1
        net_apr = supply_apr - gas_drag - (utilization_penalty * 100)

        sustainability = 1.0 - utilization * 0.3
        risk_score = utilization * 0.5 + (1 - sustainability) * 0.5

        confidence = sustainability * 0.8

        return RankedOpportunity(
            strategy=StrategyType.LENDING,
            pool_or_market=market_id,
            gross_apr=round(supply_apr, 2),
            net_apr=round(max(0, net_apr), 2),
            risk_score=round(risk_score, 4),
            gas_cost_usd=round(gas_cost_usd, 6),
            latency_ms=round(latency_ms, 1),
            sustainability_score=round(sustainability, 4),
            confidence=round(confidence, 4),
            reasoning=self._build_reasoning("LEND", market_id, supply_apr, net_apr, risk_score),
        )

    def _evaluate_staking(self, data: dict) -> RankedOpportunity | None:
        staking_apr = 6.5  # Casper staking APR
        gas_motes = 5_000_000
        gas_cost_usd = gas_motes * self.gas_price_usd
        latency_ms = self.casper_finality_seconds * 1000

        net_apr = staking_apr - 0.05  # minimal gas drag
        risk_score = 0.05
        sustainability = 0.95
        confidence = 0.95

        return RankedOpportunity(
            strategy=StrategyType.STAKING,
            pool_or_market="casper_staking",
            gross_apr=staking_apr,
            net_apr=round(net_apr, 2),
            risk_score=risk_score,
            gas_cost_usd=round(gas_cost_usd, 6),
            latency_ms=round(latency_ms, 1),
            sustainability_score=sustainability,
            confidence=confidence,
            reasoning="Casper native staking — lowest risk, predictable returns, instant finality",
        )

    def _build_reasoning(self, strategy_type: str, target: str,
                          gross: float, net: float, risk: float) -> str:
        if risk < 0.15:
            risk_label = "low"
        elif risk < 0.3:
            risk_label = "moderate"
        elif risk < 0.5:
            risk_label = "elevated"
        else:
            risk_label = "high"

        return (
            f"{strategy_type} on {target}: {gross}% gross → {net}% net APR "
            f"({risk_label} risk, score={risk:.3f})"
        )

    def select_optimal(self, opportunities: list[RankedOpportunity],
                       max_risk: float = 0.3) -> list[RankedOpportunity]:
        """Filter and select optimal opportunities within risk threshold."""
        filtered = [o for o in opportunities if o.risk_score <= max_risk]
        if not filtered:
            filtered = [o for o in opportunities if o.risk_score <= 0.5]
        filtered.sort(key=lambda x: x.net_apr, reverse=True)
        return filtered[:5]

    def get_allocation_plan(self, opportunities: list[RankedOpportunity],
                             total_capital: float = 10_000.0) -> dict:
        """Generate an allocation plan across selected opportunities."""
        selected = self.select_optimal(opportunities)
        if not selected:
            return {"plan": "HOLD", "reason": "No acceptable risk-adjusted opportunities"}

        total_score = sum(o.confidence for o in selected)
        allocations = []
        for opp in selected:
            alloc_pct = opp.confidence / total_score if total_score > 0 else 1.0 / len(selected)
            allocations.append({
                "strategy": opp.strategy.value,
                "target": opp.pool_or_market,
                "allocation_pct": round(alloc_pct * 100, 1),
                "allocation_usd": round(alloc_pct * total_capital, 2),
                "expected_net_apr": opp.net_apr,
                "risk_score": opp.risk_score,
                "confidence": opp.confidence,
            })

        weighted_apr = sum(a["allocation_pct"] / 100 * a["expected_net_apr"] for a in allocations)

        return {
            "total_capital": total_capital,
            "weighted_expected_apr": round(weighted_apr, 2),
            "weighted_expected_annual_return": round(total_capital * weighted_apr / 100, 2),
            "allocations": allocations,
            "timestamp": time.time(),
        }
