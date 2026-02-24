"use client";

import { HCSMessage } from "@/app/page";

const MSG_COLORS: Record<string, string> = {
  REGISTER: "text-blue-400 bg-blue-400/10",
  TASK_REQUEST: "text-purple-400 bg-purple-400/10",
  TASK_BID: "text-cyan-400 bg-cyan-400/10",
  TASK_ASSIGN: "text-yellow-400 bg-yellow-400/10",
  TASK_RESULT: "text-green-400 bg-green-400/10",
  PAYMENT: "text-emerald-400 bg-emerald-400/10",
  HEARTBEAT: "text-gray-400 bg-gray-400/10",
};

const MSG_ICONS: Record<string, string> = {
  REGISTER: "📝",
  TASK_REQUEST: "📨",
  TASK_BID: "🤝",
  TASK_ASSIGN: "➡️",
  TASK_RESULT: "✅",
  PAYMENT: "💸",
  HEARTBEAT: "💓",
};

function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  if (diff < 1000) return "just now";
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  return `${Math.floor(diff / 3600000)}h ago`;
}

export function MessageFeed({ messages }: { messages: HCSMessage[] }) {
  const sorted = [...messages].reverse();

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#8259EF] pulse-dot" />
          HCS Message Feed
        </h3>
        <span className="text-xs text-gray-500">{messages.length} messages</span>
      </div>

      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {sorted.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            <div className="text-2xl mb-2">📡</div>
            Waiting for HCS messages…
          </div>
        ) : (
          sorted.map((msg) => {
            const color = MSG_COLORS[msg.message_type] ?? "text-gray-400 bg-gray-400/10";
            const icon = MSG_ICONS[msg.message_type] ?? "📨";
            return (
              <div
                key={msg.id}
                className="flex items-start gap-3 p-2.5 rounded-xl bg-[#0d0d1a] border border-[#1e1e3f] hover:border-[#8259EF]/30 transition-colors animate-fade-in"
              >
                <span className="text-base mt-0.5">{icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`badge rounded-md ${color} text-xs font-mono`}>
                      {msg.message_type}
                    </span>
                    <span className="text-xs text-gray-500 font-mono truncate">
                      {msg.sender}
                    </span>
                    <span className="text-xs text-gray-600 ml-auto">
                      {timeAgo(msg.consensus_timestamp)}
                    </span>
                  </div>
                  {msg.tx_id && (
                    <div className="text-xs text-gray-600 font-mono mt-1 truncate">
                      tx: {msg.tx_id}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
