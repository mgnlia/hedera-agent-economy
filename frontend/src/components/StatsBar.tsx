"use client";

import { EconomyStats } from "@/app/page";

export function StatsBar({ stats }: { stats: EconomyStats }) {
  const items = [
    {
      label: "Tasks Completed",
      value: stats.tasks_completed.toString(),
      icon: "✅",
      color: "text-green-400",
    },
    {
      label: "HBAR Settled",
      value: `${stats.total_hbar_settled.toFixed(4)} ℏ`,
      icon: "💸",
      color: "text-[#8259EF]",
    },
    {
      label: "Active Agents",
      value: `${stats.active_agents} / ${stats.total_agents}`,
      icon: "🤖",
      color: "text-blue-400",
    },
    {
      label: "Network",
      value: "Testnet",
      icon: "⛓️",
      color: "text-yellow-400",
    },
    {
      label: "Tx Cost",
      value: "~$0.0001",
      icon: "⚡",
      color: "text-cyan-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {items.map((item) => (
        <div key={item.label} className="card text-center">
          <div className="text-xl mb-1">{item.icon}</div>
          <div className={`text-lg font-bold ${item.color}`}>{item.value}</div>
          <div className="text-xs text-gray-500 mt-0.5">{item.label}</div>
        </div>
      ))}
    </div>
  );
}
