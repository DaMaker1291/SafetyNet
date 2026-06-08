"""Strategy Agent — generates DeFi strategies based on market conditions using AI/ML."""

import json
import random
from typing import Any

from market_agent import MarketSnapshot


# Simulated ML model weights (for prototype — replace with real model)
STRATEGY_WEIGHTS = {
    "yield_optimizer": {"weight": 0.35},
    "liquidity_provision": {"weight": 0.25},
    "arbitrage_detection": {"weight": 0.20},
    "risk_rebalancing": {"weight": 0.15},
    "rwa_collateralization": {"weight": 0.05},
}


class StrategyAgent:
    """Analyzes market data and generates optimal DeFi strategies."""

    def __init__(self):
        self.strategy_id_counter = 0
        self.history: list[dict] = []

    def analyze_market(self, snapshot: MarketSnapshot) -> dict[str, Any]:
        """Run ML inference on market data to determine strategy parameters."""
        price = snapshot.cspr_price_usd
        tx_count = snapshot.recent_tx_count
        sentiment = snapshot.sentiment_score

        market_regime = self._classify_regime(price, tx_count, sentiment)

        strategy_scores = {}
        for name, meta in STRATEGY_WEIGHTS.items():
            noise = random.gauss(0, 0.05)
            base = meta["weight"]
            if market_regime == "bullish":
                base += 0.1 if name == "yield_optimizer" else 0.0
                base -= 0.05 if name == "risk_rebalancing" else 0.0
            elif market_regime == "bearish":
                base += 0.15 if name == "risk_rebalancing" else 0.0
                base += 0.05 if name == "rwa_collateralization" else 0.05
            elif market_regime == "volatile":
                base += 0.1 if name == "arbitrage_detection" else 0.0
            strategy_scores[name] = max(0.0, min(1.0, base + noise))

        ranked = sorted(
            strategy_scores.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "market_regime": market_regime,
            "cspr_price_usd": price,
            "sentiment": sentiment,
            "tx_activity": tx_count,
            "ranked_strategies": [
                {"name": n, "confidence": round(s, 4)} for n, s in ranked
            ],
            "recommended": ranked[0][0] if ranked else "hold",
        }

    def _classify_regime(
        self, price: float, tx_count: int, sentiment: float
    ) -> str:
        """Classify market regime based on signals."""
        if price > 0.1 and sentiment > 0.7:
            return "bullish"
        elif price < 0.03 or sentiment < 0.3:
            return "bearish"
        elif tx_count > 50:
            return "volatile"
        return "neutral"

    def generate_strategy(
        self, analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a concrete strategy plan from market analysis."""
        self.strategy_id_counter += 1
        recommended = analysis["recommended"]
        confidence = next(
            (s["confidence"] for s in analysis["ranked_strategies"]
             if s["name"] == recommended),
            0.0,
        )

        params = self._build_params(recommended, analysis)

        strategy = {
            "id": self.strategy_id_counter,
            "type": recommended,
            "confidence": confidence,
            "params": params,
            "market_regime": analysis["market_regime"],
            "generated_at": __import__("time").time(),
        }

        self.history.append(strategy)
        return strategy

    def _build_params(
        self, strategy_type: str, analysis: dict
    ) -> dict[str, Any]:
        """Build strategy-specific parameters."""
        base_params = {
            "max_allocation_pct": 0.3,
            "slippage_tolerance": 0.01,
            "gas_limit": 500_000_000,
        }

        if strategy_type == "yield_optimizer":
            base_params.update({
                "min_apr": 0.05 + random.random() * 0.1,
                "lockup_days": random.choice([7, 14, 30]),
                "compounding": True,
            })
        elif strategy_type == "liquidity_provision":
            base_params.update({
                "pool_type": "cspr-usdc",
                "tick_range": [0.95, 1.05],
                "fee_tier": 0.003,
            })
        elif strategy_type == "arbitrage_detection":
            base_params.update({
                "min_profit_bps": 50,
                "max_legs": 3,
                "dex_sources": ["casper-swap", "csp-dex"],
            })
        elif strategy_type == "risk_rebalancing":
            base_params.update({
                "target_allocation": {
                    "stable": 0.6,
                    "volatile": 0.3,
                    "rwa": 0.1,
                },
                "rebalance_threshold": 0.05,
            })
        elif strategy_type == "rwa_collateralization":
            base_params.update({
                "asset_type": "real_estate_token",
                "ltv_ratio": 0.6,
                "oracle_source": "chainlink",
            })

        return base_params
