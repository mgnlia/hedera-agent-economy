"""
Hedera Agent Economy — Vercel Serverless Backend
Stateless REST API with mock Hedera HCS simulation.
"""

import hashlib
import os
import time
import uuid
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel, Field

app = FastAPI(title="Hedera Agent Economy API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mock state ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

MOCK_AGENTS = [
    {"agent_id": "registry-001", "agent_type": "registry", "name": "Registry Agent",
     "skills": ["register", "discover"], "hbar_balance": 50.0, "tasks_completed": 142,
     "earnings_hbar": 0.0, "status": "idle"},
    {"agent_id": "broker-001", "agent_type": "broker", "name": "Broker Agent",
     "skills": ["match", "assign", "route"], "hbar_balance": 25.0, "tasks_completed": 98,
     "earnings_hbar": 0.0, "status": "idle"},
    {"agent_id": "worker-summarizer", "agent_type": "worker", "name": "Summarizer Agent",
     "skills": ["summarize", "tldr", "abstract"], "hbar_balance": 18.5, "tasks_completed": 67,
     "earnings_hbar": 33.5, "status": "idle"},
    {"agent_id": "worker-reviewer", "agent_type": "worker", "name": "Code Reviewer Agent",
     "skills": ["review", "lint", "security-scan"], "hbar_balance": 22.1, "tasks_completed": 54,
     "earnings_hbar": 27.0, "status": "idle"},
    {"agent_id": "worker-analyst", "agent_type": "worker", "name": "Data Analyst Agent",
     "skills": ["analyze", "stats", "chart"], "hbar_balance": 15.8, "tasks_completed": 41,
     "earnings_hbar": 20.5, "status": "idle"},
    {"agent_id": "settlement-001", "agent_type": "settlement", "name": "Settlement Agent",
     "skills": ["settle", "pay", "transfer"], "hbar_balance": 100.0, "tasks_completed": 162,
     "earnings_hbar": 0.0, "status": "idle"},
]

MOCK_TOPICS = {
    "registry": "0.0.4821901",
    "tasks": "0.0.4821902",
    "results": "0.0.4821903",
    "payments": "0.0.4821904",
}


def mock_messages(limit: int = 20) -> list:
    now = time.time()
    types = ["REGISTER", "TASK_REQUEST", "TASK_ASSIGN", "TASK_RESULT", "PAYMENT", "HEARTBEAT"]
    agents = ["registry-001", "broker-001", "worker-summarizer", "worker-reviewer", "worker-analyst"]
    topics = ["registry", "tasks", "results", "payments"]
    msgs = []
    for i in range(min(limit, 20)):
        t = now - (i * 12)
        msgs.append({
            "id": hashlib.md5(f"{t}{i}".encode()).hexdigest()[:8],
            "topic": topics[i % len(topics)],
            "sender": agents[i % len(agents)],
            "message_type": types[i % len(types)],
            "payload": {"seq": i, "ts": t},
            "sequence_number": 200 - i,
            "consensus_timestamp": datetime.utcfromtimestamp(t).isoformat(),
            "tx_id": f"0.0.5483526@{int(t)}.{i:06d}",
        })
    return msgs


def mock_transactions(limit: int = 10) -> list:
    now = time.time()
    task_types = ["summarize", "review", "analyze"]
    workers = ["worker-summarizer", "worker-reviewer", "worker-analyst"]
    txns = []
    for i in range(min(limit, 10)):
        t = now - (i * 45)
        txns.append({
            "task_id": hashlib.md5(f"task{t}{i}".encode()).hexdigest()[:12],
            "task_type": task_types[i % 3],
            "worker_id": workers[i % 3],
            "cost_hbar": round(0.3 + (i % 5) * 0.15, 2),
            "duration_ms": 400 + (i * 87) % 600,
            "status": "completed",
            "completed_at": datetime.utcfromtimestamp(t).isoformat(),
            "tx_id": f"0.0.5483526@{int(t)}.settle",
        })
    return txns


# ── Models ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    task_type: str
    payload: str
    budget_hbar: float = 0.5
    requester: str = "user"


# ── Endpoints ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agents": len(MOCK_AGENTS),
        "network": "testnet",
        "mock_mode": True,
        "topics": MOCK_TOPICS,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/state")
async def get_state():
    return {
        "agents": MOCK_AGENTS,
        "messages": mock_messages(20),
        "transactions": mock_transactions(10),
        "stats": {
            "tasks_completed": 362,
            "total_hbar_settled": 81.0,
            "active_agents": len(MOCK_AGENTS),
            "total_agents": len(MOCK_AGENTS),
            "topics": MOCK_TOPICS,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/agents")
async def list_agents():
    return {"agents": MOCK_AGENTS, "count": len(MOCK_AGENTS)}


@app.get("/messages")
async def get_messages(limit: int = 50):
    msgs = mock_messages(min(limit, 50))
    return {"messages": msgs, "total": len(msgs)}


@app.get("/transactions")
async def get_transactions(limit: int = 20):
    txns = mock_transactions(min(limit, 20))
    return {"transactions": txns, "total": len(txns)}


@app.post("/task")
async def submit_task(req: TaskRequest):
    task_map = {
        "summarize": "worker-summarizer",
        "review": "worker-reviewer",
        "analyze": "worker-analyst",
    }
    worker_id = task_map.get(req.task_type, "worker-analyst")
    cost = round(req.budget_hbar * 0.8, 4)
    duration = 450 + abs(hash(req.payload)) % 500

    result_templates = {
        "summarize": f"Summary: Key points extracted from '{req.payload[:60]}' — multi-agent coordination enables trustless task delegation with HBAR micropayments settled via HCS.",
        "review": f"Code Review: Analyzed '{req.payload[:60]}' — No critical vulnerabilities found. Recommend input validation on boundary conditions. Gas optimization possible in iteration loops.",
        "analyze": f"Analysis: Processed '{req.payload[:60]}' — Trend shows 23% growth. Peak activity detected at index 4. Recommend scaling infrastructure for projected 40% increase.",
    }
    result_text = result_templates.get(req.task_type, f"Task '{req.task_type}' completed successfully.")

    return {
        "task_id": req.task_id,
        "worker_id": worker_id,
        "task_type": req.task_type,
        "result": result_text,
        "cost_hbar": cost,
        "duration_ms": duration,
        "completed_at": datetime.utcnow().isoformat(),
        "tx_id": f"0.0.5483526@{int(time.time())}.{req.task_id}",
        "status": "completed",
    }


@app.post("/demo/run")
async def run_demo():
    demo_tasks = [
        TaskRequest(task_type="summarize", payload="Summarize the Hedera whitepaper key points", budget_hbar=0.5),
        TaskRequest(task_type="review", payload="Review this Solidity contract for reentrancy vulnerabilities", budget_hbar=1.0),
        TaskRequest(task_type="analyze", payload="Analyze daily active users trend: [120,145,132,178,201]", budget_hbar=0.75),
    ]
    results = []
    for task in demo_tasks:
        result = await submit_task(task)
        results.append(result)
    return {"demo": "complete", "tasks_executed": len(results), "results": results}


# Vercel handler
handler = Mangum(app, lifespan="off")
