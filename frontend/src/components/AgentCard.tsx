"use client";

import { Agent } from "@/app/page";

const TYPE_ICONS: Record<string, string> = {
  registry: "📋",
  broker: "🔀",
  worker: "⚙️",
  settlement: "💸",
};

const TYPE_COLORS: Record<string, string> = {
  registry: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  broker: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  worker: "text-green-400 bg-green-400/10 border-green-400/20",
  settlement: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20",
};

const STATUS_COLORS: Record<string, string> = {
  idle: "bg-green-400",
  busy: "bg-yellow-400 animate-pulse",
  offline: "bg-gray-600",
};

export function AgentCard({ agent }: { agent: Agent }) {
  const icon = TYPE_ICONS[agent.agent_type] ?? "🤖";
  const colorClass = TYPE_COLORS[agent.agent_type] ?? "text-gray-400 bg-gray-400/10 border-gray-400/20";
  const statusColor = STATUS_COLORS[agent.status] ?? "bg-gray-600";

  return (
    <div className="card hover:border-[#8259EF]/40 transition-colors animate-fade-in">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{icon}</span>
          <div>
            <div className="text-sm font-semibold text-white">{agent.name}</div>
            <div className="text-xs text-gray-500 font-mono">{agent.agent_id}</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${statusColor}`} />
          <span className="text-xs text-gray-400 capitalize">{agent.status}</span>
        </div>
      </div>

      {/* Skills */}
      <div className="flex flex-wrap gap-1 mb-3">
        {agent.skills.map((skill) => (
          <span key={skill} className={`badge border ${colorClass} text-xs`}>
            {skill}
          </span>
        ))}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-[#0d0d1a] rounded-lg p-2 text-center">
          <div className="text-gray-400">Tasks</div>
          <div className="text-white font-bold text-base">{agent.tasks_completed}</div>
        </div>
        <div className="bg-[#0d0d1a] rounded-lg p-2 text-center">
          <div className="text-gray-400">Earned</div>
          <div className="text-[#8259EF] font-bold text-base">
            {agent.earnings_hbar.toFixed(3)} ℏ
          </div>
        </div>
      </div>
    </div>
  );
}
