"""
Hedera Agent Economy — Vercel Serverless Backend
Simulates the multi-agent coordination layer on Hedera Consensus Service.

API contract matches the frontend EconomySnapshot interface exactly.
"""
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel

app = FastAPI(
    title="Hedera Agent Economy API",
    version="2.0.0",
    description="Multi-agent coordination layer using Hedera Consensus Service",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Simulated state ────────────────────────────────────────────────────────

AGENTS: list[dict] = [
    {
        "agent_id": "registry-001",
        "agent_type": "registry",
        "name": "Registry Agent",
        "skills": ["discover", "register", "lookup"],
        "hbar_balance": 50.0,
        "tasks_completed": 142,
        "earnings_hbar": 28.4,
        "status": "idle",
        "registered_at": "2026-02-24T10:00:00Z",
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
        "registered_at": "2026-02-24T10:00:00Z",
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
        "registered_at": "2026-02-24T10:00:00Z",
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
        "registered_at": "2026-02-24T10:00:00Z",
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
        "registered_at": "2026-02-24T10:00:00Z",
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
        "registered_at": "2026-02-24T10:00:00Z",
    },
]

MESSAGES: list[dict] = [
    {
        "id": "msg-001",
        "topic": "agent-registry",
        "sender": "registry-001",
        "message_type": "agent_registered",
        "payload": {"agent_id": "worker-summarizer", "skills": ["summarize", "tldr"]},
        "consensus_timestamp": "2026-02-24T10:00:00Z",
        "tx_id": "0.0.5483526@1708765200.000000000",
    },
    {
        "id": "msg-002",
        "topic": "task-negotiation",
        "sender": "broker-001",
        "message_type": "task_assigned",
        "payload": {"task_id": "task-abc", "worker": "worker-summarizer", "budget_hbar": 0.5},
        "consensus_timestamp": "2026-02-24T10:01:00Z",
        "tx_id": "0.0.5483526@1708765260.000000000",
    },
    {
        "id": "msg-003",
        "topic": "settlement",
        "sender": "settlement-001",
        "message_type": "payment_settled",
        "payload": {"task_id": "task-abc", "amount_hbar": 0.5, "tx_id": "0.0.5483526@1708765200.000000000"},
        "consensus_timestamp": "2026-02-24T10:02:00Z",
        "tx_id": "0.0.5483526@1708765320.000000000",
    },
]

TRANSACTIONS: list[dict] = [
    {
        "task_id": "task-abc",
        "worker_id": "worker-summarizer",
        "amount_hbar": 0.5,
        "tx_id": "0.0.5483526@1708765200.000000000",
        "duration_ms": 312,
        "timestamp": 1708765200,
        "mock": True,
    },
    {
        "task_id": "task-def",
        "worker_id": "worker-code-reviewer",
        "amount_hbar": 1.0,
        "tx_id": "0.0.5483526@1708765260.000000000",
        "duration_ms": 428,
        "timestamp": 1708765260,
        "mock": True,
    },
    {
        "task_id": "task-ghi",
        "worker_id": "worker-data-analyst",
        "amount_hbar": 0.75,
        "tx_id": "0.0.5483526@1708765320.000000000",
        "duration_ms": 389,
        "timestamp": 1708765320,
        "mock": True,
    },
]

# Cumulative counters (seeded with pre-existing demo data)
_tasks_completed = sum(a["tasks_completed"] for a in AGENTS)
_total_hbar_settled = sum(t["amount_hbar"] for t in TRANSACTIONS)

HCS_TOPICS = {
    "agent-registry": "0.0.5483527",
    "task-negotiation": "0.0.5483528",
    "settlement": "0.0.5483529",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _economy_snapshot() -> dict:
    active = sum(1 for a in AGENTS if a["status"] == "busy")
    return {
        "agents": AGENTS,
        "messages": MESSAGES[-50:],
        "transactions": TRANSACTIONS[-20:],
        "stats": {
            "tasks_completed": _tasks_completed,
            "total_hbar_settled": round(_total_hbar_settled, 4),
            "active_agents": active,
            "total_agents": len(AGENTS),
            "topics": HCS_TOPICS,
        },
        "timestamp": _now(),
    }


# ── Models ─────────────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    task_type: str
    payload: str
    budget_hbar: float = 0.5


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "hedera_network": os.getenv("HEDERA_NETWORK", "testnet"),
        "topic_id": "0.0.demo",
        "agents_registered": len(AGENTS),
        "demo_mode": True,
        "ai_enabled": False,
        "timestamp": _now(),
    }


@app.get("/state")
def get_state():
    """Return full EconomySnapshot — primary endpoint polled by the frontend."""
    return _economy_snapshot()


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


# Legacy routes kept for backwards compat
@app.get("/stats")
def get_stats():
    snap = _economy_snapshot()
    s = snap["stats"]
    return {
        "total_agents": s["total_agents"],
        "total_tasks": s["tasks_completed"],
        "completed_tasks": s["tasks_completed"],
        "pending_tasks": 0,
        "failed_tasks": 0,
        "total_hbar_settled": s["total_hbar_settled"],
        "hcs_messages": len(MESSAGES),
        "topic_id": "0.0.demo",
        "demo_mode": True,
    }


@app.get("/feed")
def get_feed(limit: int = 50):
    return {"messages": MESSAGES[-limit:], "topic_id": "0.0.demo", "count": len(MESSAGES)}


@app.post("/task")
@app.post("/tasks/submit")
def submit_task(req: TaskRequest):
    """Submit a task to the broker for agent matching and execution."""
    global _tasks_completed, _total_hbar_settled

    task_id = f"task-{str(uuid.uuid4())[:8]}"
    start_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

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
    assigned_worker_id = skill_map.get(req.task_type, "worker-summarizer")
    worker = next((a for a in AGENTS if a["agent_id"] == assigned_worker_id), AGENTS[2])

    result_map = {
        "summarize": f"Summary: {req.payload[:120]}… [AI condensed to 3 key points via HCS-verified consensus]",
        "review": f"Code Review: 0 critical issues detected. 2 style suggestions. Reentrancy pattern flagged for: {req.payload[:80]}",
        "analyze": f"Analysis complete: Dataset shows upward trend. Mean={random.randint(100, 500)}, σ={random.randint(10, 50)}. Confidence: 94%",
    }
    result_text = result_map.get(req.task_type, f"Task completed: {req.payload[:100]}")

    ts = int(datetime.now(timezone.utc).timestamp())
    tx_id = f"0.0.5483526@{ts}.000000000"
    duration_ms = random.randint(280, 650)

    # Update global state
    _tasks_completed += 1
    _total_hbar_settled = round(_total_hbar_settled + req.budget_hbar, 4)
    worker["tasks_completed"] += 1
    worker["earnings_hbar"] = round(worker["earnings_hbar"] + req.budget_hbar, 4)

    TRANSACTIONS.append({
        "task_id": task_id,
        "worker_id": assigned_worker_id,
        "amount_hbar": req.budget_hbar,
        "tx_id": tx_id,
        "duration_ms": duration_ms,
        "timestamp": ts,
        "mock": True,
    })

    MESSAGES.append({
        "id": f"msg-{str(uuid.uuid4())[:6]}",
        "topic": "task-negotiation",
        "sender": "broker-001",
        "message_type": "task_completed",
        "payload": {"task_id": task_id, "worker": assigned_worker_id, "result": result_text[:80]},
        "consensus_timestamp": datetime.now(timezone.utc).isoformat(),
        "tx_id": tx_id,
    })

    return {
        "task_id": task_id,
        "status": "completed",
        "result": result_text,
        "cost_hbar": req.budget_hbar,
        "duration_ms": duration_ms,
        "assigned_to": worker["name"],
        "tx_id": tx_id,
        "hcs_sequence": 1000 + len(MESSAGES),
    }


@app.post("/demo/run")
def run_demo():
    """Trigger a full demo cycle — 3 tasks across all worker types."""
    demo_tasks = [
        TaskRequest(task_type="summarize", payload="Summarize the Hedera whitepaper key points on hashgraph consensus", budget_hbar=0.5),
        TaskRequest(task_type="review", payload="Review this Solidity contract for reentrancy vulnerabilities", budget_hbar=1.0),
        TaskRequest(task_type="analyze", payload="Analyze daily active users trend: [120,145,132,178,201,189,224]", budget_hbar=0.75),
    ]
    results = [submit_task(task) for task in demo_tasks]
    return {
        "demo": "complete",
        "tasks_executed": len(results),
        "total_hbar_spent": sum(r["cost_hbar"] for r in results),
        "results": results,
    }


handler = Mangum(app, lifespan="off")
