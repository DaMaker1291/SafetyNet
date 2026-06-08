"""Tests for StrategyAgent."""

import sys
sys.path.insert(0, "../agent")

from market_agent import MarketSnapshot
from strategy_agent import StrategyAgent


def make_snapshot(
    price=0.042, tx_count=128, sentiment=0.65
) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=1000.0,
        cspr_price_usd=price,
        cspr_volume_24h=1_500_000,
        cspr_market_cap=150_000_000,
        total_contracts=42,
        recent_tx_count=tx_count,
        avg_gas_price=0.1,
        top_pools_volume=[],
        sentiment_score=sentiment,
    )


def test_strategy_agent_initialization():
    agent = StrategyAgent()
    assert agent.strategy_id_counter == 0
    assert agent.history == []


def test_market_analysis_bullish():
    agent = StrategyAgent()
    snapshot = make_snapshot(price=0.12, sentiment=0.85, tx_count=200)
    analysis = agent.analyze_market(snapshot)
    assert analysis["market_regime"] == "bullish"
    assert analysis["recommended"] != ""
    assert len(analysis["ranked_strategies"]) == 5


def test_market_analysis_bearish():
    agent = StrategyAgent()
    snapshot = make_snapshot(price=0.02, sentiment=0.2, tx_count=10)
    analysis = agent.analyze_market(snapshot)
    assert analysis["market_regime"] == "bearish"


def test_generate_strategy():
    agent = StrategyAgent()
    snapshot = make_snapshot()
    analysis = agent.analyze_market(snapshot)
    strategy = agent.generate_strategy(analysis)
    assert strategy["id"] == 1
    assert strategy["type"] in [
        "yield_optimizer", "liquidity_provision",
        "arbitrage_detection", "risk_rebalancing",
        "rwa_collateralization",
    ]
    assert "params" in strategy
    assert strategy["confidence"] > 0
    assert len(agent.history) == 1


def test_multiple_strategies_increment():
    agent = StrategyAgent()
    snapshot = make_snapshot()
    for i in range(3):
        analysis = agent.analyze_market(snapshot)
        strategy = agent.generate_strategy(analysis)
        assert strategy["id"] == i + 1
    assert len(agent.history) == 3
