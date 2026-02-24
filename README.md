# 🤖 Hedera Agent Economy

> **Multi-agent coordination layer using Hedera Consensus Service (HCS) as the message bus for agent discovery, task negotiation, and HBAR micropayment settlement.**

Built for the [Hedera Hello Future Apex Hackathon 2026](https://hackathon.stackup.dev/web/events/hedera-hello-future-apex-hackathon-2026) — **AI & Agents Track** ($48K prize pool).

[![Live Demo](https://img.shields.io/badge/Live_Demo-Vercel-black?logo=vercel)](https://hedera-agent-economy.vercel.app)
[![Backend](https://img.shields.io/badge/Backend-Railway-purple)](https://hedera-agent-economy-production.up.railway.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Dashboard                         │
│          Live HCS feed · Agent status · Task UI             │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST + WebSocket
┌───────────────────────▼─────────────────────────────────────┐
│                   FastAPI Backend                            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Registry     │  │ Broker       │  │ Settlement       │  │
│  │ Agent        │  │ Agent        │  │ Agent            │  │
│  │              │  │              │  │                  │  │
│  │ Publishes    │  │ Matches      │  │ Triggers HBAR    │  │
│  │ capabilities │  │ tasks →      │  │ micropayments    │  │
│  │ to HCS       │  │ workers      │  │ via HTS          │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘  │
│         │                 │                 │               │
│  ┌──────▼─────────────────▼─────────────────▼───────────┐  │
│  │              Worker Agents (Claude AI)                 │  │
│  │  • summarizer   • code-reviewer   • data-analyst      │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Hedera Consensus Service (HCS)                  │
│                                                             │
│  Topics:  registry · tasks · results · payments             │
│  Finality: 3-5 seconds  |  Cost: ~$0.0001/msg               │
└─────────────────────────────────────────────────────────────┘
```

## 🌟 Key Features

| Feature | Description |
|---------|-------------|
| **HCS Message Bus** | All agent coordination via Hedera Consensus Service — immutable, ordered, verifiable |
| **Agent Discovery** | Registry agent broadcasts capabilities; broker matches tasks to workers |
| **AI Task Execution** | Workers use Claude AI for summarization, code review, and data analysis |
| **HBAR Settlement** | Automatic micropayment settlement after every completed task |
| **Live Dashboard** | Real-time WebSocket feed of HCS messages, agent status, and transaction log |
| **Testnet Ready** | Full end-to-end on Hedera testnet — no real money required |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, `uv` package manager
- Node.js 18+
- Free Hedera testnet account ([portal.hedera.com](https://portal.hedera.com))
- Anthropic API key

### Backend

```bash
cd backend
cp ../.env.example .env
# Fill in HEDERA_ACCOUNT_ID, HEDERA_PRIVATE_KEY, ANTHROPIC_API_KEY

uv sync
uv run uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## 🤖 Agent Types

### Registry Agent
Posts agent capability listings to HCS `registry` topic every 30 seconds. Any agent can discover available workers by reading the topic from the Hedera Mirror Node.

### Broker Agent
Receives task requests via REST API, finds the best matching idle worker (by skills + task count), assigns the task via HCS `tasks` topic, and returns the result.

### Worker Agents (3 types)
| Worker | Skills | AI Model |
|--------|--------|----------|
| `summarizer` | summarize, tldr, abstract | Claude 3.5 Haiku |
| `code-reviewer` | review, lint, security-scan | Claude 3.5 Haiku |
| `data-analyst` | analyze, stats, chart | Claude 3.5 Haiku |

### Settlement Agent
Triggers HBAR micropayment via Hedera Token Service after every `TASK_RESULT` message. Records settlement on HCS `payments` topic for auditability.

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/state` | GET | Full economy snapshot |
| `/agents` | GET | List all agents |
| `/task` | POST | Submit a task |
| `/messages` | GET | HCS message history |
| `/transactions` | GET | Settlement history |
| `/demo/run` | POST | Run full demo cycle |
| `/ws` | WS | Live state feed |

### Submit a Task

```bash
curl -X POST https://hedera-agent-economy-production.up.railway.app/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "summarize",
    "payload": "Summarize the Hedera whitepaper",
    "budget_hbar": 0.5
  }'
```

## 🏆 Why Hedera?

1. **Finality in 3-5s** — agents get confirmed task assignments in seconds, not minutes
2. **Predictable fees** — HCS messages cost ~$0.0001, enabling true micropayments
3. **Auditability** — every agent action is permanently recorded on a public ledger
4. **No mining** — aBFT consensus means no forks, no reorgs, no uncertainty
5. **HBAR settlement** — native token transfers complete in the same 3-5s window

## 📁 Project Structure

```
hedera-agent-economy/
├── backend/
│   ├── main.py              # FastAPI app + lifespan
│   ├── models.py            # Pydantic models + EconomyState
│   ├── hedera_client.py     # HCS client (SDK + Mirror Node)
│   ├── agents/
│   │   ├── base.py          # BaseAgent class
│   │   ├── registry.py      # RegistryAgent
│   │   ├── broker.py        # BrokerAgent
│   │   ├── worker.py        # WorkerAgent (Claude AI)
│   │   └── settlement.py    # SettlementAgent
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx         # Main dashboard
│   │   └── layout.tsx
│   └── src/components/
│       ├── AgentCard.tsx
│       ├── MessageFeed.tsx
│       ├── StatsBar.tsx
│       ├── TaskSubmitter.tsx
│       ├── TransactionLog.tsx
│       └── EconomyChart.tsx
├── .env.example
└── README.md
```

## 🔗 Links

- **Live Demo:** https://hedera-agent-economy.vercel.app
- **API Docs:** https://hedera-agent-economy-production.up.railway.app/docs
- **Hedera Portal:** https://portal.hedera.com
- **Mirror Node:** https://testnet.mirrornode.hedera.com

## 📄 License

MIT
