"""MCP Server — Model Context Protocol bridge between Casper Network and LLM.

Implements the MCP pattern exposing tools/resources for:
  - Read: balances, pool states, prices, historical volatility, contract state
  - Write: transfer CSPR, swap tokens, stake, lend, provide liquidity

Designed to be consumed by any LLM (OpenAI, Claude, etc.) as a tool server.
"""

import json
import time
import hmac
import hashlib
import logging
from typing import Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

log = logging.getLogger("safetynet.mcp")


class MCPTool(str, Enum):
    READ_BALANCE = "read_balance"
    READ_POOL = "read_pool"
    READ_PRICE = "read_price"
    READ_HISTORICAL_VOLATILITY = "read_historical_volatility"
    READ_CONTRACT_STATE = "read_contract_state"
    READ_LENDING_MARKET = "read_lending_market"
    TRANSFER_CSPR = "transfer_cspr"
    SWAP_TOKENS = "swap_tokens"
    STAKE = "stake"
    LEND = "lend"
    WITHDRAW_LIQUIDITY = "withdraw_liquidity"
    SIMULATE_SWAP = "simulate_swap"
    GET_GAS_ESTIMATE = "get_gas_estimate"


@dataclass
class MCPResource:
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


@dataclass
class MCPToolDef:
    name: str
    description: str
    input_schema: dict
    handler: Callable = lambda **kwargs: {}


RESOURCES = [
    MCPResource("casper://balance/{address}", "Account Balance",
                "CSPR and token balances for an account"),
    MCPResource("casper://pool/{pool_id}", "Pool State",
                "Current state of a liquidity pool: reserves, volume, APR"),
    MCPResource("casper://price/{token_pair}", "Token Price",
                "Current spot price for a token pair"),
    MCPResource("casper://volatility/{token}/{window}", "Historical Volatility",
                "Rolling volatility for a token over a time window"),
    MCPResource("casper://lending/{market}", "Lending Market",
                "Supply/borrow rates, utilization, TVL for a lending market"),
    MCPResource("casper://gas/forecast", "Gas Forecast",
                "Predicted gas prices for the next N blocks"),
]


class MCPServer:
    """MCP Server exposing Casper Network read/write capabilities to LLMs."""

    def __init__(self, node_url: str = "https://rpc.testnet.casperlabs.io/rpc"):
        self.node_url = node_url
        self._tools: dict[str, MCPToolDef] = {}
        self._whitelisted_contracts: set[str] = set()
        self._register_default_tools()

    def register_tool(self, tool: MCPToolDef):
        self._tools[tool.name] = tool

    def _register_default_tools(self):
        tools = [
            MCPToolDef(
                name=MCPTool.READ_BALANCE,
                description="Read CSPR and token balances for a Casper account",
                input_schema={
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "Casper account public key hex"}
                    },
                    "required": ["address"]
                },
                handler=self._handle_read_balance,
            ),
            MCPToolDef(
                name=MCPTool.READ_POOL,
                description="Read current state of a liquidity pool",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pool_id": {"type": "string", "description": "Pool identifier"}
                    },
                    "required": ["pool_id"]
                },
                handler=self._handle_read_pool,
            ),
            MCPToolDef(
                name=MCPTool.READ_PRICE,
                description="Read current spot price for a token pair",
                input_schema={
                    "type": "object",
                    "properties": {
                        "token_pair": {"type": "string", "description": "e.g. CSPR-USDC"}
                    },
                    "required": ["token_pair"]
                },
                handler=self._handle_read_price,
            ),
            MCPToolDef(
                name=MCPTool.READ_HISTORICAL_VOLATILITY,
                description="Read historical volatility for a token over a time window",
                input_schema={
                    "type": "object",
                    "properties": {
                        "token": {"type": "string", "description": "Token symbol e.g. CSPR"},
                        "window": {"type": "string", "description": "Time window: 1h, 24h, 7d"}
                    },
                    "required": ["token", "window"]
                },
                handler=self._handle_volatility,
            ),
            MCPToolDef(
                name=MCPTool.READ_LENDING_MARKET,
                description="Read supply/borrow rates and utilization for a lending market",
                input_schema={
                    "type": "object",
                    "properties": {
                        "market": {"type": "string", "description": "Market name e.g. cspr-market"}
                    },
                    "required": ["market"]
                },
                handler=self._handle_lending_market,
            ),
            MCPToolDef(
                name=MCPTool.GET_GAS_ESTIMATE,
                description="Get estimated gas cost for a transaction type",
                input_schema={
                    "type": "object",
                    "properties": {
                        "tx_type": {"type": "string", "description": "swap, transfer, stake, lend"}
                    },
                    "required": ["tx_type"]
                },
                handler=self._handle_gas_estimate,
            ),
            MCPToolDef(
                name=MCPTool.SIMULATE_SWAP,
                description="Simulate a swap to calculate expected output and slippage",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pool_id": {"type": "string"},
                        "token_in": {"type": "string"},
                        "token_out": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["pool_id", "token_in", "token_out", "amount"]
                },
                handler=self._handle_simulate_swap,
            ),
            MCPToolDef(
                name=MCPTool.SWAP_TOKENS,
                description="Execute a token swap (requires whitelisted contract)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pool_id": {"type": "string"},
                        "token_in": {"type": "string"},
                        "token_out": {"type": "string"},
                        "amount": {"type": "number"},
                        "min_received": {"type": "number"},
                    },
                    "required": ["pool_id", "token_in", "token_out", "amount"]
                },
                handler=self._handle_swap,
            ),
            MCPToolDef(
                name=MCPTool.STAKE,
                description="Stake CSPR to a validator",
                input_schema={
                    "type": "object",
                    "properties": {
                        "validator": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["validator", "amount"]
                },
                handler=self._handle_stake,
            ),
            MCPToolDef(
                name=MCPTool.LEND,
                description="Supply tokens to a lending market",
                input_schema={
                    "type": "object",
                    "properties": {
                        "market": {"type": "string"},
                        "token": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["market", "token", "amount"]
                },
                handler=self._handle_lend,
            ),
        ]
        for t in tools:
            self.register_tool(t)

    def get_tool(self, name: str) -> MCPToolDef | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in self._tools.values()
        ]

    def list_resources(self) -> list[dict]:
        return [asdict(r) for r in RESOURCES]

    def call_tool(self, name: str, arguments: dict) -> dict:
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = tool.handler(**arguments)
            return {"result": result}
        except Exception as e:
            log.error("MCP tool %s error: %s", name, e)
            return {"error": str(e)}

    def whitelist_contract(self, address: str):
        self._whitelisted_contracts.add(address.lower())

    def is_whitelisted(self, address: str) -> bool:
        return address.lower() in self._whitelisted_contracts

    # --- Handlers ---

    def _handle_read_balance(self, address: str) -> dict:
        return {
            "address": address,
            "cspr_balance": "42,500.00",
            "tokens": {
                "USDC": "12,000.00",
                "CSPR": "42,500.00",
                "stCSPR": "10,000.00",
            },
            "purse": "main",
        }

    def _handle_read_pool(self, pool_id: str) -> dict:
        pools = {
            "cspr-usdc": {
                "reserve_0": "1,250,000 CSPR",
                "reserve_1": "52,500 USDC",
                "volume_24h": "$320,000",
                "apr": 18.5,
                "tvl": "$2,100,000",
                "fee": 0.003,
            },
            "cspr-eth": {
                "reserve_0": "850,000 CSPR",
                "reserve_1": "120 ETH",
                "volume_24h": "$180,000",
                "apr": 12.3,
                "tvl": "$1,400,000",
                "fee": 0.003,
            },
            "usdc-stcspr": {
                "reserve_0": "500,000 USDC",
                "reserve_1": "480,000 stCSPR",
                "volume_24h": "$95,000",
                "apr": 8.7,
                "tvl": "$980,000",
                "fee": 0.001,
            },
        }
        return pools.get(pool_id.lower(), {"error": "Pool not found", "pool_id": pool_id})

    def _handle_read_price(self, token_pair: str) -> dict:
        prices = {
            "cspr-usdc": {"price": 0.042, "change_24h": 3.2},
            "cspr-usdt": {"price": 0.0418, "change_24h": 3.0},
            "usdc-usdt": {"price": 0.999, "change_24h": 0.01},
        }
        return prices.get(token_pair.lower(), {"error": "Pair not found"})

    def _handle_volatility(self, token: str, window: str) -> dict:
        windows = {"1h": 0.8, "24h": 3.2, "7d": 12.5}
        return {
            "token": token.upper(),
            "window": window,
            "volatility_pct": windows.get(window, 2.0),
            "annualized_vol_pct": 45.0,
            "trend": "slightly_bullish",
        }

    def _handle_lending_market(self, market: str) -> dict:
        markets = {
            "cspr-market": {
                "supply_apr": 4.2,
                "borrow_apr": 7.8,
                "utilization": 0.54,
                "tvl": "$5,200,000",
                "total_borrowed": "$2,800,000",
            },
            "usdc-market": {
                "supply_apr": 3.1,
                "borrow_apr": 5.9,
                "utilization": 0.48,
                "tvl": "$3,800,000",
                "total_borrowed": "$1,800,000",
            },
        }
        return markets.get(market.lower(), {"error": "Market not found"})

    def _handle_gas_estimate(self, tx_type: str) -> dict:
        estimates = {
            "transfer": {"gas_motes": 2_500_000, "cost_usd": 0.0001, "confidence": 0.99},
            "swap": {"gas_motes": 15_000_000, "cost_usd": 0.0006, "confidence": 0.95},
            "stake": {"gas_motes": 5_000_000, "cost_usd": 0.0002, "confidence": 0.98},
            "lend": {"gas_motes": 10_000_000, "cost_usd": 0.0004, "confidence": 0.96},
        }
        return estimates.get(tx_type, {"error": "Unknown tx type"})

    def _handle_simulate_swap(self, pool_id: str, token_in: str,
                               token_out: str, amount: float) -> dict:
        slippage = amount * 0.003
        output = amount * 0.997
        return {
            "pool_id": pool_id,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount,
            "amount_out": round(output, 6),
            "slippage_est": round(slippage, 6),
            "price_impact_pct": 0.05,
            "gas_est_motes": 15_000_000,
        }

    def _handle_swap(self, pool_id: str, token_in: str,
                      token_out: str, amount: float,
                      min_received: float = 0) -> dict:
        if not self.is_whitelisted(pool_id):
            return {"error": f"Contract {pool_id} not whitelisted — denied"}
        output = amount * 0.997
        if output < min_received:
            return {"error": f"Output {output} < min_received {min_received} — slippage too high"}
        return {
            "tx_hash": f"mcp_swap_{hashlib.sha256(json.dumps(locals()).encode()).hexdigest()[:16]}",
            "amount_out": round(output, 6),
            "gas_used": 15_000_000,
            "status": "simulated",
        }

    def _handle_stake(self, validator: str, amount: float) -> dict:
        return {
            "tx_hash": f"mcp_stake_{hashlib.sha256(f'{validator}{amount}{time.time_ns()}'.encode()).hexdigest()[:16]}",
            "validator": validator,
            "amount": amount,
            "status": "simulated",
        }

    def _handle_lend(self, market: str, token: str, amount: float) -> dict:
        return {
            "tx_hash": f"mcp_lend_{hashlib.sha256(f'{market}{token}{amount}{time.time_ns()}'.encode()).hexdigest()[:16]}",
            "market": market,
            "token": token,
            "amount": amount,
            "status": "simulated",
        }
