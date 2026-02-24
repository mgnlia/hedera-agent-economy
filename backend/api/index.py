"""
Hedera Agent Economy — Vercel Serverless Entry Point
Simplified stateless API for demo/hackathon deployment.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import time
import uuid
import random
from datetime import datetime

app = FastAPI(
    title="Hedera Agent Economy API",
    version="1.0.0",
    description="Multi-agent coordination layer using Hedera Consensus Service"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEDERA_ACCOUNT_ID = os.getenv("HEDERA_ACCOUNT_ID", "0.0.5483526")
HEDERA_NETWORK = os.getenv("HEDERA_NETWORK", "testnet")

# Mock agent registry
AGENTS = [
    {"agent_id": "registry-001", "agent_type": "registry", "name": "Registry Agent", "status": "idle", "skills": ["register", "discover", "list"], "tasks_completed": 0, "hbar_earned": 0.0},
    {"agent_id": "broker-001", "agent_type": "broker", "name": "Broker Agent", "status": "idle", "skills": ["match", "assign", "route"], "tasks_completed": 0, "hbar_earned": 0.0},
    {"agent_id": "settlement-001", "agent_type": "settlement", "name": "Settlement Agent", "status": "idle", "skills": ["pay", "verify", "escrow"], "tasks_completed": 0, "hbar_earned": 0.0},
    {"agent_id": "worker-summarizer", "agent_type": "worker", "name": "Summarizer Worker", "status": "idle", "skills": ["summarize", "tldr", "abstract"], "tasks_completed": 12, "hbar_earned": 6.0},
    {"agent_id": "worker-reviewer", "agent_type": "worker", "name": "Code Reviewer Worker", "status": "idle", "skills": ["review", "lint", "security-scan"], "tasks_completed": 8, "hbar_earned": 8.0},
    {"agent_id": "worker-analyst", "agent_type": "worker", "name": "Data Analyst Worker", "status": "idle", "skills": ["analyze", "stats", "chart"], "tasks_completed": 15, "hbar_earned": 11.25},
]

MOCK_MESSAGES = [
    {"type": "AGENT_REGISTER", "agent": "Registry Agent", "topic": "registry", "timestamp": "2026-02-24T10:00:01Z"},
    {"type": "AGENT_REGISTER", "agent": "Broker Agent", "topic": "registry", "timestamp": "2026-02-24T10:00:02Z"},
    {"type": "AGENT_REGISTER", "agent": "Summarizer Worker", "topic": "registry", "timestamp": "2026-02-24T10:00:03Z"},
    {"type": "TASK_REQUEST", "task_type": "summarize", "budget_hbar": 0.5, "topic": "tasks", "timestamp": "2026-02-24T10:01:00Z"},
    {"type": "TASK_ASSIGN", "worker": "worker-summarizer", "task_type": "summarize", "topic": "tasks", "timestamp": "2026-02-24T10:01:01Z"},
    {"type": "TASK_RESULT", "worker": "worker-summarizer", "cost_hbar": 0.4, "status": "success", "topic": "results", "timestamp": "2026-02-24T10:01:05Z"},
    {"type": "PAYMENT_SETTLED", "amount_hbar": 0.4, "from": "requester", "to": "worker-summarizer", "topic": "payments", "timestamp": "2026-02-24T10:01:06Z"},
]

MOCK_TRANSACTIONS = [
    {"tx_id": "0.0.5483526@1708768800.000001", "type": "PAYMENT", "amount_hbar": 0.4, "from": "0.0.requester", "to": "0.0.worker-1", "status": "SUCCESS", "timestamp": "2026-02-24T10:01:06Z"},
    {"tx_id": "0.0.5483526@1708768860.000002", "type": "PAYMENT", "amount_hbar": 1.0, "from": "0.0.requester", "to": "0.0.worker-2", "status": "SUCCESS", "timestamp": "2026-02-24T10:02:06Z"},
    {"tx_id": "0.0.5483526@1708768920.000003", "type": "PAYMENT", "amount_hbar": 0.75, "from": "0.0.requester", "to": "0.0.worker-3", "status": "SUCCESS", "timestamp": "2026-02-24T10:03:06Z"},
]

MOCK_TOPICS = {
    "registry": "0.0.4891234",
    "tasks": "0.0.4891235",
    "results": "0.0.4891236",
    "payments": "0.0.4891237",
}


class TaskRequest(BaseModel):
    task_type: str
    payload: str
    budget_hbar: float = 0.5
    requester: str = "api-user"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "agents": len(AGENTS),
        "network": HEDERA_NETWORK,
        "account_id": HEDERA_ACCOUNT_ID,
        "topics": MOCK_TOPICS,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/state")
def get_state():
    return {
        "agents": AGENTS,
        "agent_count": len(AGENTS),
        "messages": MOCK_MESSAGES,
        "transactions": MOCK_TRANSACTIONS,
        "topics": MOCK_TOPICS,
        "total_hbar_settled": sum(t["amount_hbar"] for t in MOCK_TRANSACTIONS),
        "network": HEDERA_NETWORK,
        "account_id": HEDERA_ACCOUNT_ID,
        "mock_mode": not bool(os.getenv("HEDERA_PRIVATE_KEY")),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/task")
def submit_task(req: TaskRequest):
    task_id = str(uuid.uuid4())[:8]
    
    # Find a capable worker
    workers = [a for a in AGENTS if a["agent_type"] == "worker"]
    matched = next(
        (w for w in workers if any(s in req.task_type for s in w["skills"])),
        workers[0] if workers else None
    )
    
    cost = round(req.budget_hbar * 0.8, 4)
    duration_ms = 450
    
    task_results = {
        "summarize": f"Summary: The provided content discusses key concepts and delivers actionable insights. Main points: (1) Core functionality is well-defined, (2) Implementation follows best practices, (3) Further optimization opportunities exist. [Task {task_id}]",
        "review": f"Code Review: No critical security vulnerabilities found. Minor issues: (1) Missing input validation on line 42, (2) Consider extracting helper function for reuse, (3) Add error handling for edge cases. Recommendation: Approve with minor changes. [Task {task_id}]",
        "analyze": f"Analysis: Dataset shows positive trend with 23% growth over the period. Key metrics: Mean=156.2, Std Dev=28.4, Trend=+2.3/period. Anomaly detected at index 4 — likely organic spike. Confidence: 94%. [Task {task_id}]",
    }
    
    result_text = task_results.get(
        req.task_type,
        f"Task completed successfully. Processed: '{req.payload[:80]}' — Analysis complete with high confidence. [Task {task_id}]"
    )
    
    tx_id = f"0.0.5483526@{int(time.time())}.{task_id}"
    
    return {
        "task_id": task_id,
        "status": "success",
        "worker_id": matched["agent_id"] if matched else "worker-analyst",
        "worker_name": matched["name"] if matched else "Data Analyst Worker",
        "task_type": req.task_type,
        "result": result_text,
        "cost_hbar": cost,
        "duration_ms": duration_ms,
        "hcs_tx_id": tx_id,
        "topic_id": MOCK_TOPICS.get("results", "0.0.4891236"),
        "settled": True,
        "network": HEDERA_NETWORK,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/agents")
def list_agents():
    return {
        "agents": AGENTS,
        "count": len(AGENTS),
    }


@app.get("/messages")
def get_messages(limit: int = 50):
    msgs = MOCK_MESSAGES[-limit:]
    return {"messages": msgs, "total": len(MOCK_MESSAGES)}


@app.get("/transactions")
def get_transactions(limit: int = 20):
    txns = MOCK_TRANSACTIONS[-limit:]
    return {"transactions": txns, "total": len(MOCK_TRANSACTIONS)}


@app.post("/demo/run")
def run_demo():
    demo_tasks = [
        TaskRequest(task_type="summarize", payload="Summarize the Hedera whitepaper key points", budget_hbar=0.5),
        TaskRequest(task_type="review", payload="Review this Solidity contract for reentrancy vulnerabilities", budget_hbar=1.0),
        TaskRequest(task_type="analyze", payload="Analyze daily active users trend: [120,145,132,178,201]", budget_hbar=0.75),
    ]
    
    results = []
    for req in demo_tasks:
        result = submit_task(req)
        results.append(result)
    
    return {
        "demo": "complete",
        "tasks_executed": len(results),
        "total_hbar_spent": sum(r["cost_hbar"] for r in results),
        "results": results,
    }


# Mangum adapter for Vercel serverless
from mangum import Mangum
handler = Mangum(app, lifespan="off")
