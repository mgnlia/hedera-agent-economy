"""
Settlement Agent — triggers HBAR micropayments via Hedera Token Service.
Listens for TASK_RESULT messages and settles payment to the worker.
"""

import asyncio
import time
from agents.base import BaseAgent
from hedera_client import HederaClient
from models import EconomyState


class SettlementAgent(BaseAgent):
    def __init__(self, hedera: HederaClient, economy_state: EconomyState):
        super().__init__(
            hedera=hedera,
            economy_state=economy_state,
            agent_type="settlement",
            name="Settlement Agent",
            skills=["pay", "settle", "transfer"],
        )
        self._settlement_queue: asyncio.Queue = asyncio.Queue()

    async def run(self):
        self.log("Starting — ready to settle HBAR payments")
        while self.running:
            try:
                settlement = await asyncio.wait_for(
                    self._settlement_queue.get(), timeout=5.0
                )
                await self._settle(settlement)
            except asyncio.TimeoutError:
                pass

    async def settle_task(self, task_id: str, worker_id: str, amount_hbar: float) -> str:
        """
        Settle payment for a completed task.
        Returns Hedera transaction ID.
        """
        self.set_status("busy")
        start = time.time()

        try:
            # Get worker's Hedera account (in production, workers register their account IDs)
            # For demo, we use the operator account and record the settlement on-chain via HCS
            worker_account = self._get_worker_account(worker_id)

            # Execute HBAR transfer
            tx_id = await self.hedera.transfer_hbar(worker_account, amount_hbar)

            # Record settlement on HCS payments topic
            await self.publish("payments", "PAYMENT", {
                "task_id": task_id,
                "worker_id": worker_id,
                "worker_account": worker_account,
                "amount_hbar": amount_hbar,
                "tx_id": tx_id,
                "settled_at": time.time(),
            })

            # Update economy stats
            self.state.total_hbar_settled += amount_hbar
            self.state.add_transaction({
                "task_id": task_id,
                "worker_id": worker_id,
                "amount_hbar": amount_hbar,
                "tx_id": tx_id,
                "duration_ms": int((time.time() - start) * 1000),
                "timestamp": time.time(),
                "network": self.hedera.network,
                "mock": self.hedera.is_mock,
            })

            self.log(
                f"Settled {amount_hbar} HBAR for task {task_id} → {worker_id} "
                f"(tx: {tx_id}, {'MOCK' if self.hedera.is_mock else 'LIVE'})"
            )
            return tx_id

        except Exception as e:
            self.log(f"Settlement failed for task {task_id}: {e}")
            raise
        finally:
            self.set_status("idle")

    def _get_worker_account(self, worker_id: str) -> str:
        """
        Look up a worker's Hedera account ID.
        In production, workers register their account IDs on startup.
        For demo, we use the operator account.
        """
        # Workers would register their accounts on the registry topic
        # For now, return the operator account (funds stay in same account for demo)
        return self.hedera.account_id

    async def _settle(self, settlement: dict):
        await self.settle_task(
            settlement["task_id"],
            settlement["worker_id"],
            settlement["amount_hbar"],
        )

    async def queue_settlement(self, task_id: str, worker_id: str, amount_hbar: float):
        """Queue a settlement for async processing."""
        await self._settlement_queue.put({
            "task_id": task_id,
            "worker_id": worker_id,
            "amount_hbar": amount_hbar,
        })
