"""
Hedera Agent Economy — Vercel Serverless Backend
Simulates the multi-agent coordination layer on Hedera Consensus Service.
"""
import os
import random
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel

app = FastAPI(
    title="Hedera Agent Economy API",
    version="1.0.0",
    description="Multi-agent coordination layer using Hedera Consensus Service",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Simulated agent state ──────────────────────────────────────────────────

AGENTS = [
    {
        "agent_id": "registry-001",
        "agent_type": "registry",
        "name": "Registry Agent",
        "skills": ["discover", "register", "lookup"],
        "hbar_balance": 50.0,
        "tasks_completed": 142,
        "earnings_hbar": 28.4,
        "status": "idle",
    },
    {
        "agent_id": "broker-001",
        "agent_type": "broker",
        "name": "Broker Agent",
        "skills": ["match", "negotiate", "route"],
        "hbar_balance": 75.2,
        "tasks_completed": 138,
        "earnings_hbar": 55.1,
        "status": "busy",
    },
    {
        "agent_id": "worker-summarizer",
        "agent_type": "worker",
        "name": "Summarizer Worker",
        "skills": ["summarize", "tldr", "abstract"],
        "hbar_balance": 22.5,
        "tasks_completed": 89,
        "earnings_hbar": 44.5,
        "status": "idle",
    },
    {
        "agent_id": "worker-code-reviewer",
        "agent_type": "worker",
        "name": "Code Reviewer Worker",
        "skills": ["review", "lint", "security-scan"],
        "hbar_balance": 31.0,
        "tasks_completed": 67,
        "earnings_hbar": 67.0,
        "status": "idle",
    },
    {
        "agent_id": "worker-data-analyst",
        "agent_type": "worker",
        "name": "Data Analyst Worker",
        "skills": ["analyze", "stats", "chart"],
        "hbar_balance": 18.7,
        "tasks_completed": 54,
        "earnings_hbar": 40.5,
        "status": "busy",
    },
    {
        "agent_id": "settlement-001",
        "agent_type": "settlement",
        "name": "Settlement Agent",
        "skills": ["settle", "transfer", "audit"],
        "hbar_balance": 200.0,
        "tasks_completed": 308,
        "earnings_hbar": 15.4,
        "status": "idle",
    },
]

MESSAGES: list[dict] = [
    {
        "id": "msg-001",
        "topic": "agent-registry",
        "sender": "registry-001",
        "message_type": "agent_registered",
        "payload": {"agent_id": "worker-summarizer", "skills": ["summarize", "tldr"]},
        "timestamp": "2026-02-24T10:00:00Z",
        "hcs_sequence": 1001,
    },
    {
        "id": "msg-002",
        "topic": "task-negotiation",
        "sender": "broker-001",
        "message_type": "task_assigned",
        "payload": {"task_id": "task-abc", "worker": "worker-summarizer", "budget_hbar": 0.5},
        "timestamp": "2026-02-24T10:01:00Z",
        "hcs_sequence": 1002,
    },
    {
        "id": "msg-003",
        "topic": "settlement",
        "sender": "settlement-001",
        "message_type": "payment_settled",
        "payload": {"task_id": "task-abc", "amount_hbar": 0.5, "tx_id": "0.0.5483526@1708765200.000000000"},
        "timestamp": "2026-02-24T10:02:00Z",
        "hcs_sequence": 1003,
    },
]

TRANSACTIONS: list[dict] = [
    {
        "tx_id": "0.0.5483526@1708765200.000000000",
        "from_agent": "broker-001",
        "to_agent": "worker-summarizer",
        "amount_hbar": 0.5,
        "task_id": "task-abc",
        "status": "confirmed",
        "timestamp": "2026-02-24T10:02:00Z",
    },
    {
        "tx_id": "0.0.5483526@1708765260.000000000",
        "from_agent": "broker-001",
        "to_agent": "worker-code-reviewer",
        "amount_hbar": 1.0,
        "task_id": "task-def",
        "status": "confirmed",
        "timestamp": "2026-02-24T10:05:00Z",
    },
    {
        "tx_id": "0.0.5483526@1708765320.000000000",
        "from_agent": "broker-001",
        "to_agent": "worker-data-analyst",
        "amount_hbar": 0.75,
        "task_id": "task-ghi",
        "status": "confirmed",
        "timestamp": "2026-02-24T10:08:00Z",
    },
]


class TaskRequest(BaseModel):
    task_type: str
    payload: str
    budget_hbar: float = 0.5


# ── Routes ─────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {
        "status": "ok",
        "agents": len(AGENTS),
        "network": os.getenv("HEDERA_NETWORK", "testnet"),
        "account_id": os.getenv("HEDERA_ACCOUNT_ID", "0.0.5483526"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/state")
def get_state():
    return {
        "agents": AGENTS,
        "agent_count": len(AGENTS),
        "message_count": len(MESSAGES),
        "transaction_count": len(TRANSACTIONS),
        "total_hbar_settled": sum(t["amount_hbar"] for t in TRANSACTIONS),
        "network": os.getenv("HEDERA_NETWORK", "testnet"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/agents")
def list_agents():
    return {"agents": AGENTS, "count": len(AGENTS)}


@app.get("/messages")
def get_messages(limit: int = 50):
    msgs = MESSAGES[-limit:]
    return {"messages": msgs, "total": len(MESSAGES)}


@app.get("/transactions")
def get_transactions(limit: int = 20):
    txns = TRANSACTIONS[-limit:]
    return {"transactions": txns, "total": len(TRANSACTIONS)}


@app.post("/task")
def submit_task(req: TaskRequest):
    """Submit a task to the broker for agent matching and execution."""
    task_id = f"task-{str(uuid.uuid4())[:8]}"

    # Find matching worker
    skill_map = {
        "summarize": "worker-summarizer",
        "tldr": "worker-summarizer",
        "abstract": "worker-summarizer",
        "review": "worker-code-reviewer",
        "lint": "worker-code-reviewer",
        "security-scan": "worker-code-reviewer",
        "analyze": "worker-data-analyst",
        "stats": "worker-data-analyst",
        "chart": "worker-data-analyst",
    }
    assigned_worker = skill_map.get(req.task_type, "worker-summarizer")

    worker = next((a for a in AGENTS if a["agent_id"] == assigned_worker), AGENTS[2])

    # Simulate result
    result_map = {
        "summarize": f"Summary: {req.payload[:100]}... [AI condensed to 3 key points]",
        "review": f"Code Review: Found 0 critical issues. 2 style suggestions for: {req.payload[:80]}",
        "analyze": f"Analysis: Dataset shows upward trend. Mean: {random.randint(100, 500)}, Std: {random.randint(10, 50)}",
    }
    result_text = result_map.get(req.task_type, f"Task completed: {req.payload[:100]}")

    tx_id = f"0.0.5483526@{int(datetime.utcnow().timestamp())}.000000000"

    new_tx = {
        "tx_id": tx_id,
        "from_agent": "broker-001",
        "to_agent": assigned_worker,
        "amount_hbar": req.budget_hbar,
        "task_id": task_id,
        "status": "confirmed",
        "timestamp": datetime.utcnow().isoformat(),
    }
    TRANSACTIONS.append(new_tx)

    new_msg = {
        "id": f"msg-{str(uuid.uuid4())[:6]}",
        "topic": "task-negotiation",
        "sender": "broker-001",
        "message_type": "task_completed",
        "payload": {"task_id": task_id, "worker": assigned_worker, "result": result_text[:80]},
        "timestamp": datetime.utcnow().isoformat(),
        "hcs_sequence": 1000 + len(MESSAGES) + 1,
    }
    MESSAGES.append(new_msg)

    return {
        "task_id": task_id,
        "status": "completed",
        "assigned_to": worker["name"],
        "result": result_text,
        "hbar_paid": req.budget_hbar,
        "tx_id": tx_id,
        "hcs_sequence": new_msg["hcs_sequence"],
    }


@app.post("/demo/run")
def run_demo():
    """Trigger a full demo cycle."""
    demo_tasks = [
        TaskRequest(task_type="summarize", payload="Summarize the Hedera whitepaper key points", budget_hbar=0.5),
        TaskRequest(task_type="review", payload="Review this Solidity contract for reentrancy vulnerabilities", budget_hbar=1.0),
        TaskRequest(task_type="analyze", payload="Analyze daily active users trend: [120,145,132,178,201]", budget_hbar=0.75),
    ]

    results = [submit_task(task) for task in demo_tasks]
    return {"demo": "complete", "tasks_executed": len(results), "results": results}


handler = Mangum(app, lifespan="off")
