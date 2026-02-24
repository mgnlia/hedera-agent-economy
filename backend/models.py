"""Shared data models for the Agent Economy."""

import time
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    agent_id: str
    agent_type: str  # registry | broker | worker | settlement
    name: str
    skills: list[str] = []
    hbar_balance: float = 10.0
    tasks_completed: int = 0
    earnings_hbar: float = 0.0
    status: Literal["idle", "busy", "offline"] = "idle"
    registered_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return self.model_dump()


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    topic: str
    sender: str
    message_type: Literal[
        "REGISTER", "TASK_REQUEST", "TASK_BID", "TASK_ASSIGN",
        "TASK_RESULT", "PAYMENT", "HEARTBEAT"
    ]
    payload: dict[str, Any] = {}
    sequence_number: int = 0
    consensus_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tx_id: str | None = None


class TaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    task_type: str
    payload: str
    budget_hbar: float = 0.5
    requester: str = "user"
    submitted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskResult(BaseModel):
    task_id: str
    worker_id: str
    task_type: str
    result: str
    cost_hbar: float
    duration_ms: int
    completed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tx_id: str | None = None
    status: Literal["completed", "failed"] = "completed"


class EconomyState:
    """In-memory economy state — shared across all agents."""

    def __init__(self):
        self.agents: dict[str, AgentCapability] = {}
        self.messages: list[AgentMessage] = []
        self.transactions: list[dict] = []
        self.tasks_completed: int = 0
        self.total_hbar_settled: float = 0.0
        self.topics: dict[str, str] = {}  # name -> topic_id
        self.started_at = datetime.utcnow().isoformat()

    def register_agent(self, agent: AgentCapability):
        self.agents[agent.agent_id] = agent

    def add_message(self, msg: AgentMessage):
        self.messages.append(msg)
        if len(self.messages) > 500:
            self.messages = self.messages[-500:]

    def add_transaction(self, txn: dict):
        self.transactions.append(txn)
        if len(self.transactions) > 200:
            self.transactions = self.transactions[-200:]

    def snapshot(self) -> dict:
        return {
            "agents": [a.to_dict() for a in self.agents.values()],
            "messages": [m.dict() for m in self.messages[-20:]],
            "transactions": self.transactions[-10:],
            "stats": {
                "tasks_completed": self.tasks_completed,
                "total_hbar_settled": round(self.total_hbar_settled, 4),
                "active_agents": sum(1 for a in self.agents.values() if a.status != "offline"),
                "total_agents": len(self.agents),
                "topics": self.topics,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
