"""Base agent class for all economy agents."""

import asyncio
import uuid
from datetime import datetime

from models import AgentCapability, AgentMessage, EconomyState
from hedera_client import HederaClient


class BaseAgent:
    def __init__(
        self,
        hedera: HederaClient,
        economy_state: EconomyState,
        agent_type: str,
        name: str,
        skills: list[str] = [],
    ):
        self.agent_id = f"{agent_type}-{str(uuid.uuid4())[:6]}"
        self.agent_type = agent_type
        self.name = name
        self.skills = skills
        self.hedera = hedera
        self.state = economy_state
        self.running = True

        self.capability = AgentCapability(
            agent_id=self.agent_id,
            agent_type=agent_type,
            name=name,
            skills=skills,
            hbar_balance=10.0,
        )
        self.state.register_agent(self.capability)

    async def run(self):
        """Main agent loop — override in subclass."""
        raise NotImplementedError

    async def publish(self, topic: str, msg_type: str, payload: dict) -> str:
        """Publish a message to an HCS topic."""
        msg = AgentMessage(
            topic=topic,
            sender=self.agent_id,
            message_type=msg_type,
            payload=payload,
        )
        tx_id = await self.hedera.submit_message(topic, msg.dict())
        msg.tx_id = tx_id
        self.state.add_message(msg)
        return tx_id

    def set_status(self, status: str):
        self.capability.status = status

    def log(self, msg: str):
        print(f"[{self.agent_type.upper()}:{self.agent_id}] {msg}")
