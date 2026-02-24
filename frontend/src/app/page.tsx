"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { AgentCard } from "@/components/AgentCard";
import { MessageFeed } from "@/components/MessageFeed";
import { StatsBar } from "@/components/StatsBar";
import { TaskSubmitter } from "@/components/TaskSubmitter";
import { TransactionLog } from "@/components/TransactionLog";
import { EconomyChart } from "@/components/EconomyChart";
import { HederaLogo } from "@/components/HederaLogo";

const API = process.env.NEXT_PUBLIC_API_URL || "https://hedera-vercel-backend.vercel.app";

export interface Agent {
  agent_id: string;
  agent_type: string;
  name: string;
  skills: string[];
  hbar_balance: number;
  tasks_completed: number;
  earnings_hbar: number;
  status: "idle" | "busy" | "offline";
  registered_at: string;
}

export interface HCSMessage {
  id: string;
  topic: string;
  sender: string;
  message_type: string;
  payload: Record<string, unknown>;
  consensus_timestamp: string;
  tx_id: string | null;
}

export interface Transaction {
  task_id: string;
  worker_id: string;
  amount_hbar: number;
  tx_id: string;
  duration_ms: number;
  timestamp: number;
  mock: boolean;
}

export interface EconomyStats {
  tasks_completed: number;
  total_hbar_settled: number;
  active_agents: number;
  total_agents: number;
  topics: Record<string, string>;
}

export interface EconomySnapshot {
  agents: Agent[];
  messages: HCSMessage[];
  transactions: Transaction[];
  stats: EconomyStats;
  timestamp: string;
}

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState<EconomySnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [wsError, setWsError] = useState(false);
  const [taskHistory, setTaskHistory] = useState<number[]>([]);
  const [hbarHistory, setHbarHistory] = useState<number[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchSnapshot = useCallback(async () => {
    try {
      const res = await fetch(`${API}/state`);
      if (res.ok) {
        const data: EconomySnapshot = await res.json();
        setSnapshot(data);
        setTaskHistory(h => [...h.slice(-20), data.stats.tasks_completed]);
        setHbarHistory(h => [...h.slice(-20), data.stats.total_hbar_settled]);
      }
    } catch (_) {}
  }, []);

  // WebSocket connection with polling fallback
  useEffect(() => {
    const wsUrl = API.replace("https://", "wss://").replace("http://", "ws://") + "/ws";

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          setWsError(false);
          if (pollRef.current) clearInterval(pollRef.current);
        };

        ws.onmessage = (e) => {
          try {
            const data: EconomySnapshot = JSON.parse(e.data);
            setSnapshot(data);
            setTaskHistory(h => [...h.slice(-20), data.stats.tasks_completed]);
            setHbarHistory(h => [...h.slice(-20), data.stats.total_hbar_settled]);
          } catch (_) {}
        };

        ws.onclose = () => {
          setConnected(false);
          // Fall back to polling
          pollRef.current = setInterval(fetchSnapshot, 3000);
          setTimeout(connect, 5000);
        };

        ws.onerror = () => {
          setWsError(true);
          ws.close();
        };
      } catch (_) {
        setWsError(true);
        pollRef.current = setInterval(fetchSnapshot, 3000);
      }
    };

    connect();
    fetchSnapshot();

    return () => {
      wsRef.current?.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchSnapshot]);

  const runDemo = async () => {
    try {
      await fetch(`${API}/demo/run`, { method: "POST" });
    } catch (_) {}
  };

  const agents = snapshot?.agents ?? [];
  const messages = snapshot?.messages ?? [];
  const transactions = snapshot?.transactions ?? [];
  const stats = snapshot?.stats ?? {
    tasks_completed: 0,
    total_hbar_settled: 0,
    active_agents: 0,
    total_agents: 0,
    topics: {},
  };

  return (
    <div className="min-h-screen bg-[#0d0d1a] text-gray-100">
      {/* Header */}
      <header className="border-b border-[#1e1e3f] bg-[#0d0d1a]/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <HederaLogo />
            <div>
              <h1 className="text-lg font-bold text-white">Agent Economy</h1>
              <p className="text-xs text-gray-400">Hedera Consensus Service · Testnet</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Connection status */}
            <div className="flex items-center gap-2 text-xs">
              <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-400 pulse-dot" : "bg-yellow-400"}`} />
              <span className="text-gray-400">{connected ? "Live" : "Polling"}</span>
            </div>

            {/* Network badge */}
            <span className="badge bg-[#8259EF]/20 text-[#a78bfa]">
              Testnet
            </span>

            <button onClick={runDemo} className="btn-primary text-xs">
              ▶ Run Demo
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Stats bar */}
        <StatsBar stats={stats} />

        {/* HCS Topics */}
        {Object.keys(stats.topics).length > 0 && (
          <div className="card">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              HCS Topics
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(stats.topics).map(([name, id]) => (
                <div key={name} className="flex items-center gap-2 bg-[#0d0d1a] rounded-lg px-3 py-1.5 border border-[#1e1e3f]">
                  <span className="text-xs text-[#8259EF] font-mono">{name}</span>
                  <span className="text-xs text-gray-500 font-mono">{id}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Agents */}
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Agents ({agents.length})
            </h2>
            {agents.length === 0 ? (
              <div className="card text-center py-10 text-gray-500 text-sm">
                <div className="text-3xl mb-2">🤖</div>
                Waiting for agents to register…
              </div>
            ) : (
              agents.map((agent) => (
                <AgentCard key={agent.agent_id} agent={agent} />
              ))
            )}
          </div>

          {/* Right: Feed + Chart */}
          <div className="lg:col-span-2 space-y-6">
            {/* Economy chart */}
            <EconomyChart taskHistory={taskHistory} hbarHistory={hbarHistory} />

            {/* Task submitter */}
            <TaskSubmitter apiUrl={API} onTaskSubmitted={fetchSnapshot} />

            {/* HCS Message feed */}
            <MessageFeed messages={messages} />

            {/* Transaction log */}
            <TransactionLog transactions={transactions} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1e1e3f] mt-12 py-6 text-center text-xs text-gray-600">
        Built for{" "}
        <a href="https://hackathon.stackup.dev/web/events/hedera-hello-future-apex-hackathon-2026"
          className="text-[#8259EF] hover:underline" target="_blank" rel="noopener noreferrer">
          Hedera Hello Future Apex Hackathon 2026
        </a>{" "}
        · AI &amp; Agents Track · Powered by Hedera Consensus Service
      </footer>
    </div>
  );
}
