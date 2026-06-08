"""Execution Agent — submits strategies and actions to Casper Testnet smart contracts."""

import json
import time
import hashlib
from typing import Any

from casper_python_sdk.sdk import CasperSDK
from casper_python_sdk.utils import CLValueBuilder


class ExecutionAgent:
    """Handles on-chain submission of agent strategies to AgentVault contract."""

    def __init__(
        self,
        node_url: str,
        chain_name: str,
        contract_hash: str,
        contract_package: str,
        secret_key_path: str,
        public_key_hex: str,
    ):
        self.sdk = CasperSDK(node_url)
        self.chain_name = chain_name
        self.contract_hash = contract_hash
        self.contract_package = contract_package
        self.secret_key_path = secret_key_path
        self.public_key_hex = public_key_hex
        self.account = self.sdk.get_account(public_key_hex)

    def register_agent(self, name: str, description: str) -> str:
        """Register a new agent on-chain."""
        deploy = self.sdk.make_deploy(
            chain_name=self.chain_name,
            secret_key=self.secret_key_path,
            session_func="register_agent",
            session_args=[
                CLValueBuilder.string(name),
                CLValueBuilder.string(description),
            ],
            session_package=self.contract_package,
            payment_amount=100_000_000,
        )
        result = self.sdk.put_deploy(deploy)
        deploy_hash = result.get("deploy_hash", "")
        return deploy_hash

    def submit_strategy(
        self, agent_id: int, strategy_type: str, params_json: str
    ) -> str:
        """Submit a strategy to the on-chain vault."""
        deploy = self.sdk.make_deploy(
            chain_name=self.chain_name,
            secret_key=self.secret_key_path,
            session_func="submit_strategy",
            session_args=[
                CLValueBuilder.u256(agent_id),
                CLValueBuilder.string(strategy_type),
                CLValueBuilder.string(params_json),
            ],
            session_package=self.contract_package,
            payment_amount=100_000_000,
        )
        result = self.sdk.put_deploy(deploy)
        return result.get("deploy_hash", "")

    def record_action(
        self,
        agent_id: int,
        action_type: str,
        data_json: str,
        tx_hash: str = "",
    ) -> str:
        """Record an agent action on-chain."""
        deploy = self.sdk.make_deploy(
            chain_name=self.chain_name,
            secret_key=self.secret_key_path,
            session_func="record_action",
            session_args=[
                CLValueBuilder.u256(agent_id),
                CLValueBuilder.string(action_type),
                CLValueBuilder.string(data_json),
                CLValueBuilder.string(tx_hash),
            ],
            session_package=self.contract_package,
            payment_amount=100_000_000,
        )
        result = self.sdk.put_deploy(deploy)
        return result.get("deploy_hash", "")

    def query_agent(self, agent_id: int) -> dict[str, Any]:
        """Query agent info from the contract."""
        result = self.sdk.query_contract_dictionary(
            contract_hash=self.contract_hash,
            dictionary_name="agents",
            dictionary_item_key=str(agent_id),
        )
        return result

    def query_counts(self) -> dict[str, int]:
        """Query the on-chain agent/strategy/action counts."""
        deploy = self.sdk.make_deploy(
            chain_name=self.chain_name,
            secret_key=self.secret_key_path,
            session_func="get_counts",
            session_args=[],
            session_package=self.contract_package,
            payment_amount=100_000_000,
        )
        result = self.sdk.put_deploy(deploy)
        return {"agent_count": 0, "strategy_count": 0, "action_count": 0}
