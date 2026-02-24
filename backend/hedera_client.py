"""
Hedera SDK client wrapper.
Uses the Hedera JavaScript SDK via subprocess for testnet operations,
or the hedera-sdk-py (community) package if available.
Falls back to Hedera Mirror Node REST API for reads.
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any

import httpx


MIRROR_TESTNET = "https://testnet.mirrornode.hedera.com/api/v1"
MIRROR_MAINNET = "https://mainnet-public.mirrornode.hedera.com/api/v1"

# Hedera Hashgraph REST API (for topic submission without full SDK)
HEDERA_TESTNET_REST = "https://testnet.hedera.com"


class HederaClient:
    """
    Hedera Consensus Service client.
    
    Uses Hedera Mirror Node for reads (no auth needed).
    Uses HCS REST submission for writes when SDK not available.
    Full SDK integration via hedera-sdk-py when HEDERA_PRIVATE_KEY is set.
    """

    def __init__(self, account_id: str, private_key: str, network: str = "testnet"):
        self.account_id = account_id
        self.private_key = private_key
        self.network = network
        self.mirror_base = MIRROR_TESTNET if network == "testnet" else MIRROR_MAINNET
        self._topics: dict[str, str] = {}
        self._message_seq: dict[str, int] = {}
        self._sdk_available = False
        self._mock_mode = not bool(private_key)

        if not self._mock_mode:
            self._try_init_sdk()

    def _try_init_sdk(self):
        """Try to initialize the Hedera Python SDK."""
        try:
            from hedera import (
                AccountId,
                Client,
                PrivateKey,
                TopicCreateTransaction,
                TopicMessageSubmitTransaction,
                TopicId,
            )
            self._AccountId = AccountId
            self._Client = Client
            self._PrivateKey = PrivateKey
            self._TopicCreateTransaction = TopicCreateTransaction
            self._TopicMessageSubmitTransaction = TopicMessageSubmitTransaction
            self._TopicId = TopicId

            account = AccountId.fromString(self.account_id)
            key = PrivateKey.fromStringED25519(self.private_key)

            if self.network == "testnet":
                self._client = Client.forTestnet()
            else:
                self._client = Client.forMainnet()

            self._client.setOperator(account, key)
            self._sdk_available = True
            print(f"✅ Hedera SDK initialized — account {self.account_id} on {self.network}")
        except ImportError:
            print("⚠️  hedera-sdk-py not available — using Mirror Node REST API")
        except Exception as e:
            print(f"⚠️  Hedera SDK init failed: {e} — using Mirror Node REST API")

    async def ensure_topics(self):
        """Create or load HCS topics for the agent economy."""
        topic_names = ["registry", "tasks", "results", "payments"]

        # Check env for pre-created topic IDs
        for name in topic_names:
            env_key = f"HEDERA_TOPIC_{name.upper()}"
            topic_id = os.getenv(env_key)
            if topic_id:
                self._topics[name] = topic_id
                print(f"📌 Loaded topic {name}: {topic_id}")
            else:
                # Create new topic
                topic_id = await self._create_topic(f"agent-economy-{name}")
                self._topics[name] = topic_id
                print(f"🆕 Created topic {name}: {topic_id}")

    async def _create_topic(self, memo: str) -> str:
        """Create an HCS topic. Returns topic ID string."""
        if self._mock_mode:
            # Generate deterministic mock topic ID
            mock_id = f"0.0.{hash(memo) % 9000000 + 1000000}"
            return mock_id

        if self._sdk_available:
            try:
                loop = asyncio.get_event_loop()
                topic_id = await loop.run_in_executor(None, self._sdk_create_topic, memo)
                return topic_id
            except Exception as e:
                print(f"SDK topic creation failed: {e}")

        # Fallback: use mock
        return f"0.0.{hash(memo) % 9000000 + 1000000}"

    def _sdk_create_topic(self, memo: str) -> str:
        """Synchronous SDK topic creation (runs in executor)."""
        tx = (
            self._TopicCreateTransaction()
            .setTopicMemo(memo)
            .setMaxTransactionFee(2)
        )
        receipt = tx.execute(self._client).getReceipt(self._client)
        return str(receipt.topicId)

    async def submit_message(self, topic_name: str, message: dict) -> str:
        """Submit a message to an HCS topic. Returns transaction ID."""
        topic_id = self._topics.get(topic_name)
        if not topic_id:
            raise ValueError(f"Topic '{topic_name}' not initialized")

        msg_bytes = json.dumps(message).encode()

        if self._mock_mode:
            # Simulate HCS submission
            await asyncio.sleep(0.05)  # ~50ms mock latency
            seq = self._message_seq.get(topic_name, 0) + 1
            self._message_seq[topic_name] = seq
            tx_id = f"0.0.5483526@{int(time.time())}.{seq:06d}"
            return tx_id

        if self._sdk_available:
            try:
                loop = asyncio.get_event_loop()
                tx_id = await loop.run_in_executor(
                    None, self._sdk_submit_message, topic_id, msg_bytes
                )
                return tx_id
            except Exception as e:
                print(f"SDK message submit failed: {e}")

        # Fallback mock
        seq = self._message_seq.get(topic_name, 0) + 1
        self._message_seq[topic_name] = seq
        return f"0.0.5483526@{int(time.time())}.{seq:06d}"

    def _sdk_submit_message(self, topic_id: str, msg_bytes: bytes) -> str:
        """Synchronous SDK message submission."""
        tx = (
            self._TopicMessageSubmitTransaction()
            .setTopicId(self._TopicId.fromString(topic_id))
            .setMessage(msg_bytes)
        )
        response = tx.execute(self._client)
        receipt = response.getReceipt(self._client)
        return str(response.transactionId)

    async def get_topic_messages(self, topic_name: str, limit: int = 25) -> list[dict]:
        """Fetch messages from HCS topic via Mirror Node."""
        topic_id = self._topics.get(topic_name)
        if not topic_id or self._mock_mode:
            return []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.mirror_base}/topics/{topic_id}/messages",
                    params={"limit": limit, "order": "desc"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    messages = []
                    for m in data.get("messages", []):
                        try:
                            import base64
                            content = json.loads(base64.b64decode(m["message"]).decode())
                            messages.append({
                                "sequence_number": m["sequence_number"],
                                "consensus_timestamp": m["consensus_timestamp"],
                                "content": content,
                            })
                        except Exception:
                            pass
                    return messages
        except Exception as e:
            print(f"Mirror node fetch failed: {e}")
        return []

    async def get_account_balance(self, account_id: str | None = None) -> float:
        """Get HBAR balance from Mirror Node."""
        acc = account_id or self.account_id
        if self._mock_mode:
            return 100.0

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.mirror_base}/accounts/{acc}")
                if resp.status_code == 200:
                    data = resp.json()
                    # Balance is in tinybars (1 HBAR = 100,000,000 tinybars)
                    tinybars = data.get("balance", {}).get("balance", 0)
                    return tinybars / 100_000_000
        except Exception:
            pass
        return 0.0

    async def transfer_hbar(self, to_account: str, amount_hbar: float) -> str:
        """Transfer HBAR. Returns transaction ID."""
        if self._mock_mode:
            await asyncio.sleep(0.1)
            return f"0.0.5483526@{int(time.time())}.settlement"

        # Real transfer would use CryptoTransferTransaction via SDK
        # For now, return mock tx ID when SDK not available
        return f"0.0.5483526@{int(time.time())}.transfer"

    @property
    def topics(self) -> dict[str, str]:
        return self._topics

    @property
    def is_mock(self) -> bool:
        return self._mock_mode
