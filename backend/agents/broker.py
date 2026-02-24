"""
Broker Agent — matches task requests to capable worker agents.
Posts task assignments to HCS tasks topic.
"""

import asyncio
import random
import time
from agents.base import BaseAgent
from hedera_client import HederaClient
from models import EconomyState, TaskRequest, TaskResult


class BrokerAgent(BaseAgent):
    def __init__(self, hedera: HederaClient, economy_state: EconomyState):
        super().__init__(
            hedera=hedera,
            economy_state=economy_state,
            agent_type="broker",
            name="Broker Agent",
            skills=["match", "assign", "route"],
        )
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._pending_results: dict[str, asyncio.Future] = {}

    async def run(self):
        self.log("Starting — ready to broker tasks")
        while self.running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=5.0)
                await self._process_task(task)
            except asyncio.TimeoutError:
                pass

    async def submit_task(self, req: TaskRequest) -> dict:
        """Accept a task, find a worker, execute, settle payment."""
        self.set_status("busy")

        # Announce task request on HCS
        await self.publish("tasks", "TASK_REQUEST", {
            "task_id": req.task_id,
            "task_type": req.task_type,
            "payload_preview": req.payload[:100],
            "budget_hbar": req.budget_hbar,
            "requester": req.requester,
        })

        # Find capable worker
        worker = self._find_worker(req.task_type)
        if not worker:
            self.set_status("idle")
            return {
                "task_id": req.task_id,
                "status": "failed",
                "error": f"No worker available for task type: {req.task_type}",
            }

        # Assign task
        await self.publish("tasks", "TASK_ASSIGN", {
            "task_id": req.task_id,
            "worker_id": worker.agent_id,
            "task_type": req.task_type,
            "budget_hbar": req.budget_hbar,
        })
        self.log(f"Assigned task {req.task_id} ({req.task_type}) → {worker.agent_id}")

        # Execute via worker
        from agents.worker import WorkerAgent
        if isinstance(worker, WorkerAgent):
            result = await worker.execute_task(req)
        else:
            result = TaskResult(
                task_id=req.task_id,
                worker_id=worker.agent_id,
                task_type=req.task_type,
                result="Task completed",
                cost_hbar=req.budget_hbar * 0.8,
                duration_ms=500,
            )

        # Post result to HCS
        await self.publish("results", "TASK_RESULT", {
            "task_id": result.task_id,
            "worker_id": result.worker_id,
            "cost_hbar": result.cost_hbar,
            "duration_ms": result.duration_ms,
            "status": result.status,
        })

        self.set_status("idle")
        return result.dict()

    def _find_worker(self, task_type: str):
        """Find an idle worker agent with matching skills."""
        from models import AgentCapability
        candidates = []
        for agent in self.state.agents.values():
            if agent.agent_type == "worker" and agent.status == "idle":
                if any(skill in task_type for skill in agent.skills):
                    candidates.append(agent.agent_id)

        if not candidates:
            # Try any idle worker
            candidates = [
                a.agent_id for a in self.state.agents.values()
                if a.agent_type == "worker" and a.status == "idle"
            ]

        if not candidates:
            return None

        # Pick least-loaded worker
        worker_id = min(
            candidates,
            key=lambda wid: self.state.agents[wid].tasks_completed
        )

        # Return the actual WorkerAgent object from main module
        import sys
        main_module = sys.modules.get("main") or sys.modules.get("__main__")
        if main_module and hasattr(main_module, "worker_agents"):
            for w in main_module.worker_agents:
                if w.agent_id == worker_id:
                    return w

        return self.state.agents.get(worker_id)

    async def _process_task(self, task: TaskRequest):
        await self.submit_task(task)
