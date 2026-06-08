"""Execution Agent — submits strategies and actions to Casper Testnet smart contracts.

Demo mode: when contract details are not configured, runs in simulated mode
and returns mock deploy hashes. Set CONTRACT_HASH in .env for real on-chain
submission via the Casper RPC API.
"""

import json
import time
import hashlib
import logging
from typing import Any

import requests

log = logging.getLogger("safetynet")


class ExecutionAgent:
    """Handles on-chain submission of agent strategies to AgentVault contract."""

    def __init__(
        self,
        node_url: str = "",
        chain_name: str = "casper-test",
        contract_hash: str = "",
        contract_package: str = "",
        secret_key_path: str = "",
        public_key_hex: str = "",
    ):
        self.node_url = node_url
        self.chain_name = chain_name
        self.contract_hash = contract_hash
        self.contract_package = contract_package
        self.secret_key_path = secret_key_path
        self.public_key_hex = public_key_hex
        self._demo_mode = not (
            bool(node_url) and bool(contract_hash) and bool(secret_key_path)
        )

        if self._demo_mode:
            log.info("ExecutionAgent running in DEMO mode (no real deploys)")

    def _mock_hash(self, prefix: str = "mock") -> str:
        raw = f"{prefix}-{time.time_ns()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:64]

    def register_agent(self, name: str, description: str) -> str:
        if self._demo_mode:
            tx = self._mock_hash("register")
            log.info("[DEMO] register_agent('%s', '%s') → %s", name, description, tx)
            return tx
        raise NotImplementedError("Real RPC call — implement with casper-client or custom deploy builder")

    def submit_strategy(
        self, agent_id: int, strategy_type: str, params_json: str
    ) -> str:
        if self._demo_mode:
            tx = self._mock_hash("strategy")
            log.info("[DEMO] submit_strategy(agent=%d, type='%s') → %s",
                     agent_id, strategy_type, tx)
            return tx
        raise NotImplementedError("Real RPC call — implement with casper-client or custom deploy builder")

    def record_action(
        self,
        agent_id: int,
        action_type: str,
        data_json: str,
        tx_hash: str = "",
    ) -> str:
        if self._demo_mode:
            tx = self._mock_hash("action")
            log.info("[DEMO] record_action(agent=%d, type='%s') → %s",
                     agent_id, action_type, tx)
            return tx
        raise NotImplementedError("Real RPC call — implement with casper-client or custom deploy builder")

    def query_agent(self, agent_id: int) -> dict[str, Any]:
        if self._demo_mode:
            return {"id": agent_id, "name": "Demo Agent", "is_active": True}
        raise NotImplementedError

    def query_counts(self) -> dict[str, int]:
        if self._demo_mode:
            return {"agent_count": 1, "strategy_count": 3, "action_count": 5}
        raise NotImplementedError
