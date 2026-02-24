"""
Worker Agent — executes tasks using Claude AI.
Skills: summarize, code-review, data-analysis.
"""

import asyncio
import os
import time
from agents.base import BaseAgent
from hedera_client import HederaClient
from models import EconomyState, TaskRequest, TaskResult

import anthropic


WORKER_PROMPTS = {
    "summarize": "You are a concise summarization agent. Summarize the following in 3-5 bullet points:",
    "tldr": "You are a TLDR agent. Give a 1-2 sentence summary of:",
    "abstract": "You are a research abstract agent. Write a structured abstract for:",
    "review": "You are a code review agent. Identify issues, bugs, and improvements in:",
    "lint": "You are a linting agent. Check for style issues and best practice violations in:",
    "security-scan": "You are a security audit agent. Find security vulnerabilities in:",
    "analyze": "You are a data analysis agent. Analyze and provide insights on:",
    "stats": "You are a statistical analysis agent. Compute key statistics for:",
    "chart": "You are a data visualization agent. Describe what charts would best represent:",
}

DEFAULT_PROMPT = "You are a helpful AI agent. Process the following task:"


class WorkerAgent(BaseAgent):
    def __init__(
        self,
        hedera: HederaClient,
        economy_state: EconomyState,
        worker_type: str,
        skills: list[str],
    ):
        super().__init__(
            hedera=hedera,
            economy_state=economy_state,
            agent_type="worker",
            name=f"Worker-{worker_type}",
            skills=skills,
        )
        self.worker_type = worker_type
        self._claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._task_queue: asyncio.Queue = asyncio.Queue()

    async def run(self):
        self.log(f"Starting — skills: {self.skills}")
        # Announce to registry
        await asyncio.sleep(1.5)
        await self.publish("registry", "REGISTER", {
            "agent_id": self.agent_id,
            "agent_type": "worker",
            "worker_type": self.worker_type,
            "skills": self.skills,
            "status": "idle",
        })

        while self.running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=5.0)
                await self.execute_task(task)
            except asyncio.TimeoutError:
                pass

    async def execute_task(self, req: TaskRequest) -> TaskResult:
        """Execute a task using Claude AI."""
        self.set_status("busy")
        start = time.time()

        try:
            # Get system prompt based on task type
            system_prompt = WORKER_PROMPTS.get(req.task_type, DEFAULT_PROMPT)

            # Call Claude
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._claude.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=512,
                    messages=[
                        {
                            "role": "user",
                            "content": f"{system_prompt}\n\n{req.payload}",
                        }
                    ],
                )
            )

            result_text = response.content[0].text
            duration_ms = int((time.time() - start) * 1000)

            # Cost is 80% of budget (worker keeps 80%, broker gets 20%)
            cost_hbar = round(req.budget_hbar * 0.8, 4)

            task_result = TaskResult(
                task_id=req.task_id,
                worker_id=self.agent_id,
                task_type=req.task_type,
                result=result_text,
                cost_hbar=cost_hbar,
                duration_ms=duration_ms,
                status="completed",
            )

            # Update agent stats
            self.capability.tasks_completed += 1
            self.capability.earnings_hbar += cost_hbar
            self.state.tasks_completed += 1

            self.log(f"Completed task {req.task_id} in {duration_ms}ms — earned {cost_hbar} HBAR")

        except Exception as e:
            self.log(f"Task {req.task_id} failed: {e}")
            task_result = TaskResult(
                task_id=req.task_id,
                worker_id=self.agent_id,
                task_type=req.task_type,
                result=f"Task failed: {str(e)[:200]}",
                cost_hbar=0.0,
                duration_ms=int((time.time() - start) * 1000),
                status="failed",
            )
        finally:
            self.set_status("idle")

        return task_result
