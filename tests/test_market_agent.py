"""Tests for MarketAgent."""

import sys
sys.path.insert(0, "../agent")

from market_agent import MarketAgent, MarketSnapshot


def test_market_snapshot_defaults():
    snapshot = MarketSnapshot(
        timestamp=1000.0,
        cspr_price_usd=0.042,
        cspr_volume_24h=1_500_000,
        cspr_market_cap=150_000_000,
        total_contracts=42,
        recent_tx_count=128,
        avg_gas_price=0.1,
        top_pools_volume=[],
        sentiment_score=0.65,
    )
    assert snapshot.cspr_price_usd == 0.042
    assert snapshot.recent_tx_count == 128
    assert snapshot.sentiment_score == 0.65
    assert isinstance(snapshot.to_dict(), dict)


def test_market_agent_initialization():
    agent = MarketAgent()
    assert agent.node_url == "https://rpc.testnet.casperlabs.io/rpc"
    assert agent.coingecko_id == "casper-network"
    assert agent.cache is None


def test_market_agent_get_snapshot():
    agent = MarketAgent()
    snapshot = agent.get_snapshot(force=True)
    assert isinstance(snapshot, MarketSnapshot)
    assert snapshot.timestamp > 0
