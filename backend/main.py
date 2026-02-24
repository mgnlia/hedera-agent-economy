"""
Hedera Agent Economy Coordinator — Backend
Multi-agent coordination layer using Hedera Consensus Service (HCS)
as the message bus for agent discovery, task negotiation, and HBAR settlement.
"""

import asyncio
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.broker import BrokerAgent
from agents.registry import RegistryAgent
from agents.settlement import SettlementAgent
from agents.worker import WorkerAgent
from hedera_client import HederaClient
from models import (
    AgentCapability,
    AgentMessage,
    EconomyState,
    TaskRequest,
    TaskResult,
)

load_dotenv()

# ── Lifespan ──────────────────────────────────────────────────────────────────

economy_state: EconomyState | None = None
hedera: HederaClient | None = None
registry_agent: RegistryAgent | None = None
broker_agent: BrokerAgent | None = None
worker_agents: list[WorkerAgent] = []
settlement_agent: SettlementAgent | None = None
ws_clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global economy_state, hedera, registry_agent, broker_agent, worker_agents, settlement_agent

    hedera = HederaClient(
        account_id=os.getenv("HEDERA_ACCOUNT_ID", "0.0.5483526"),
        private_key=os.getenv("HEDERA_PRIVATE_KEY", ""),
        network=os.getenv("HEDERA_NETWORK", "testnet"),
    )

    economy_state = EconomyState()

    # Boot agents
    registry_agent = RegistryAgent(hedera, economy_state)
    broker_agent = BrokerAgent(hedera, economy_state)
    settlement_agent = SettlementAgent(hedera, economy_state)

    worker_agents = [
        WorkerAgent(hedera, economy_state, "summarizer", ["summarize", "tldr", "abstract"]),
        WorkerAgent(hedera, economy_state, "code-reviewer", ["review", "lint", "security-scan"]),
        WorkerAgent(hedera, economy_state, "data-analyst", ["analyze", "stats", "chart"]),
    ]

    # Initialize HCS topics
    await hedera.ensure_topics()

    # Start agent loops
    asyncio.create_task(registry_agent.run())
    asyncio.create_task(broker_agent.run())
    asyncio.create_task(settlement_agent.run())
    for w in worker_agents:
        asyncio.create_task(w.run())

    # Start HCS feed broadcaster
    asyncio.create_task(broadcast_hcs_feed())

    print("✅ Agent Economy booted — all agents online")
    yield

    print("🛑 Shutting down agents")


@asynccontextmanager
async def broadcast_hcs_feed():
    pass  # placeholder — real impl below as standalone task


async def broadcast_hcs_feed():
    """Continuously poll HCS messages and broadcast to WebSocket clients."""
    while True:
        await asyncio.sleep(2)
        if economy_state and ws_clients:
            snapshot = economy_state.snapshot()
            dead = []
            for ws in ws_clients:
                try:
                    await ws.send_json(snapshot)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                ws_clients.remove(ws)


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Hedera Agent Economy API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST endpoints ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agents": len(worker_agents) + 3,
        "network": os.getenv("HEDERA_NETWORK", "testnet"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/state")
async def get_state():
    if not economy_state:
        raise HTTPException(503, "Economy not initialized")
    return economy_state.snapshot()


@app.post("/task")
async def submit_task(req: TaskRequest):
    """Submit a task to the broker for agent matching and execution."""
    if not broker_agent:
        raise HTTPException(503, "Broker not ready")
    result = await broker_agent.submit_task(req)
    return result


@app.get("/agents")
async def list_agents():
    if not economy_state:
        raise HTTPException(503, "Economy not initialized")
    return {
        "agents": [a.to_dict() for a in economy_state.agents.values()],
        "count": len(economy_state.agents),
    }


@app.get("/messages")
async def get_messages(limit: int = 50):
    if not economy_state:
        raise HTTPException(503, "Economy not initialized")
    msgs = economy_state.messages[-limit:]
    return {"messages": [m.dict() for m in msgs], "total": len(economy_state.messages)}


@app.get("/transactions")
async def get_transactions(limit: int = 20):
    if not economy_state:
        raise HTTPException(503, "Economy not initialized")
    txns = economy_state.transactions[-limit:]
    return {"transactions": txns, "total": len(economy_state.transactions)}


@app.post("/demo/run")
async def run_demo():
    """Trigger a full demo cycle: register agents, post tasks, settle payments."""
    if not broker_agent or not economy_state:
        raise HTTPException(503, "Economy not ready")

    demo_tasks = [
        TaskRequest(task_type="summarize", payload="Summarize the Hedera whitepaper key points", budget_hbar=0.5),
        TaskRequest(task_type="review", payload="Review this Solidity contract for reentrancy vulnerabilities", budget_hbar=1.0),
        TaskRequest(task_type="analyze", payload="Analyze daily active users trend from this dataset: [120,145,132,178,201]", budget_hbar=0.75),
    ]

    results = []
    for task in demo_tasks:
        result = await broker_agent.submit_task(task)
        results.append(result)
        await asyncio.sleep(0.5)

    return {"demo": "complete", "tasks_executed": len(results), "results": results}


# ── WebSocket ─────────────────────────────────────────────────────────────────


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    try:
        # Send initial state
        if economy_state:
            await ws.send_json(economy_state.snapshot())
        # Keep alive
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in ws_clients:
            ws_clients.remove(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
