"""
Registry Agent — posts capability listings to HCS registry topic.
Heartbeats every 30s to signal liveness.
"""

import asyncio
from agents.base import BaseAgent
from hedera_client import HederaClient
from models import EconomyState


class RegistryAgent(BaseAgent):
    def __init__(self, hedera: HederaClient, economy_state: EconomyState):
        super().__init__(
            hedera=hedera,
            economy_state=economy_state,
            agent_type="registry",
            name="Registry Agent",
            skills=["register", "discover", "heartbeat"],
        )
        self.heartbeat_interval = 30

    async def run(self):
        self.log("Starting — will broadcast registry heartbeats")
        # Initial registration announcement
        await asyncio.sleep(1)
        await self._announce_registry()

        while self.running:
            await asyncio.sleep(self.heartbeat_interval)
            await self._heartbeat()

    async def _announce_registry(self):
        """Announce registry is online and list all known agents."""
        known = list(self.state.agents.keys())
        await self.publish("registry", "REGISTER", {
            "registry_id": self.agent_id,
            "known_agents": known,
            "status": "online",
            "topics": self.hedera.topics,
        })
        self.log(f"Registry announced — {len(known)} agents known")

    async def _heartbeat(self):
        """Broadcast heartbeat with current agent roster."""
        agents_summary = [
            {"id": a.agent_id, "type": a.agent_type, "status": a.status, "skills": a.skills}
            for a in self.state.agents.values()
        ]
        await self.publish("registry", "HEARTBEAT", {
            "agents": agents_summary,
            "tasks_completed": self.state.tasks_completed,
            "total_hbar_settled": self.state.total_hbar_settled,
        })
        self.log(f"Heartbeat — {len(agents_summary)} agents active")

    async def register_agent(self, agent_id: str, agent_type: str, skills: list[str]) -> str:
        """Register a new agent to the registry topic."""
        tx_id = await self.publish("registry", "REGISTER", {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "skills": skills,
        })
        self.log(f"Registered agent {agent_id} ({agent_type})")
        return tx_id
