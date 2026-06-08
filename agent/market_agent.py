"""Market Agent — gathers on-chain and off-chain market data for Casper DeFi."""

import json
import time
from typing import Any
from dataclasses import dataclass, asdict

import requests


@dataclass
class MarketSnapshot:
    timestamp: float
    cspr_price_usd: float
    cspr_volume_24h: float
    cspr_market_cap: float
    total_contracts: int
    recent_tx_count: int
    avg_gas_price: float
    top_pools_volume: list[dict]
    sentiment_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarketAgent:
    """Fetches and aggregates market data for Casper ecosystem."""

    def __init__(self, node_url: str = "https://rpc.testnet.casperlabs.io/rpc"):
        self.node_url = node_url
        self.coingecko_id = "casper-network"
        self.cache: MarketSnapshot | None = None
        self.cache_ttl = 120
        self._last_fetch = 0.0

    def _call_rpc(self, method: str, params: list | None = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": method,
            "params": params or [],
        }
        resp = requests.post(self.node_url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def fetch_cspr_price(self) -> float:
        try:
            url = (f"https://api.coingecko.com/api/v3/simple/price"
                   f"?ids={self.coingecko_id}&vs_currencies=usd"
                   f"&include_24hr_vol=true&include_market_cap=true")
            data = requests.get(url, timeout=10).json()
            coin = data.get(self.coingecko_id, {})
            return coin.get("usd", 0.0)
        except Exception:
            return 0.0

    def fetch_network_stats(self) -> dict:
        try:
            info = self._call_rpc("info_get_peers")
            status = self._call_rpc("info_get_status")
            return {
                "peers": len(info.get("result", {}).get("peers", [])),
                "last_block": status.get("result", {}).get("last_added_block_info", {}),
                "uptime": status.get("result", {}).get("uptime", ""),
            }
        except Exception:
            return {}

    def scan_recent_transactions(self) -> int:
        try:
            block = self._call_rpc("chain_get_block")
            block_data = block.get("result", {}).get("block", {})
            body = block_data.get("body", {})
            deploy_hashes = body.get("deploy_hashes", [])
            return len(deploy_hashes)
        except Exception:
            return 0

    def fetch_sentiment(self) -> float:
        """Simple sentiment from social signals (placeholder)."""
        return 0.65

    def get_snapshot(self, force: bool = False) -> MarketSnapshot:
        now = time.time()
        if self.cache and not force and (now - self._last_fetch) < self.cache_ttl:
            return self.cache

        price = self.fetch_cspr_price()
        net = self.fetch_network_stats()
        tx_count = self.scan_recent_transactions()
        sentiment = self.fetch_sentiment()

        self.cache = MarketSnapshot(
            timestamp=now,
            cspr_price_usd=price,
            cspr_volume_24h=0.0,
            cspr_market_cap=0.0,
            total_contracts=net.get("peers", 0),
            recent_tx_count=tx_count,
            avg_gas_price=0.1,
            top_pools_volume=[],
            sentiment_score=sentiment,
        )
        self._last_fetch = now
        return self.cache
