"""AETHOS Agent Configuration
Environment-based configuration for the AI agent service.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Casper Network
CASPER_NODE_URL = os.getenv(
    "CASPER_NODE_URL",
    "https://rpc.testnet.casperlabs.io/rpc",
)
CASPER_NETWORK_NAME = os.getenv("CASPER_NETWORK_NAME", "casper-test")
CHAIN_NAME = os.getenv("CHAIN_NAME", "casper-test")

# Contract
CONTRACT_HASH = os.getenv("CONTRACT_HASH", "")
CONTRACT_PACKAGE = os.getenv("CONTRACT_PACKAGE", "")

# Agent keys (Testnet only — NEVER use real keys in env)
AGENT_SECRET_KEY_PATH = os.getenv(
    "AGENT_SECRET_KEY_PATH",
    "./keys/agent_secret_key.pem",
)
AGENT_PUBLIC_KEY_HEX = os.getenv("AGENT_PUBLIC_KEY_HEX", "")

# AI / ML
AI_MODEL = os.getenv("AI_MODEL", "gpt-4")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Agent behaviour
AGENT_NAME = os.getenv("AGENT_NAME", "Aethos Alpha v1")
AGENT_DESCRIPTION = os.getenv("AGENT_DESCRIPTION",
    "Autonomous DeFi strategy agent for Casper ecosystem")
STRATEGY_INTERVAL_SECONDS = int(os.getenv("STRATEGY_INTERVAL", "3600"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
