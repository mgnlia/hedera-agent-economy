"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface Props {
  taskHistory: number[];
  hbarHistory: number[];
}

export function EconomyChart({ taskHistory, hbarHistory }: Props) {
  const data = taskHistory.map((tasks, i) => ({
    t: i,
    tasks,
    hbar: hbarHistory[i] ?? 0,
  }));

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-white mb-4">📈 Economy Activity</h3>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e3f" />
            <XAxis dataKey="t" tick={{ fill: "#4b5563", fontSize: 10 }} />
            <YAxis tick={{ fill: "#4b5563", fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                background: "#13132b",
                border: "1px solid #1e1e3f",
                borderRadius: "8px",
                fontSize: "12px",
              }}
              labelStyle={{ color: "#9ca3af" }}
            />
            <Line
              type="monotone"
              dataKey="tasks"
              stroke="#8259EF"
              strokeWidth={2}
              dot={false}
              name="Tasks"
            />
            <Line
              type="monotone"
              dataKey="hbar"
              stroke="#34d399"
              strokeWidth={2}
              dot={false}
              name="HBAR settled"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex gap-4 mt-2 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-[#8259EF] inline-block" /> Tasks completed
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-emerald-400 inline-block" /> HBAR settled
        </span>
      </div>
    </div>
  );
}
