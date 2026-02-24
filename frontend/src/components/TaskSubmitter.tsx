"use client";

import { useState } from "react";

const TASK_EXAMPLES: Record<string, string> = {
  summarize: "Summarize the key innovations of Hedera Hashgraph consensus algorithm and why it achieves 10,000 TPS with finality in 3-5 seconds.",
  review: "Review this Solidity contract for vulnerabilities:\n\nfunction withdraw(uint amount) public {\n  require(balances[msg.sender] >= amount);\n  msg.sender.call{value: amount}('');\n  balances[msg.sender] -= amount;\n}",
  analyze: "Analyze this dataset of daily active users for a DeFi protocol: [1200, 1450, 1320, 1780, 2010, 1950, 2200, 2450, 2300, 2800]",
};

interface TaskResult {
  task_id: string;
  status: string;
  result?: string;
  cost_hbar?: number;
  duration_ms?: number;
  error?: string;
}

export function TaskSubmitter({
  apiUrl,
  onTaskSubmitted,
}: {
  apiUrl: string;
  onTaskSubmitted: () => void;
}) {
  const [taskType, setTaskType] = useState("summarize");
  const [payload, setPayload] = useState(TASK_EXAMPLES.summarize);
  const [budget, setBudget] = useState("0.5");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaskResult | null>(null);

  const handleTypeChange = (t: string) => {
    setTaskType(t);
    setPayload(TASK_EXAMPLES[t] ?? "");
    setResult(null);
  };

  const submit = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${apiUrl}/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: taskType,
          payload,
          budget_hbar: parseFloat(budget),
        }),
      });
      const data = await res.json();
      setResult(data);
      onTaskSubmitted();
    } catch (e) {
      setResult({ task_id: "err", status: "failed", error: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-white mb-4">Submit Task to Agent Economy</h3>

      <div className="space-y-3">
        {/* Task type */}
        <div className="flex gap-2">
          {["summarize", "review", "analyze"].map((t) => (
            <button
              key={t}
              onClick={() => handleTypeChange(t)}
              className={`flex-1 py-2 rounded-xl text-xs font-medium border transition-colors ${
                taskType === t
                  ? "bg-[#8259EF] border-[#8259EF] text-white"
                  : "border-[#1e1e3f] text-gray-400 hover:border-[#8259EF]/50"
              }`}
            >
              {t === "summarize" ? "📝 Summarize" : t === "review" ? "🔍 Code Review" : "📊 Analyze"}
            </button>
          ))}
        </div>

        {/* Payload */}
        <textarea
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
          rows={4}
          className="w-full bg-[#0d0d1a] border border-[#1e1e3f] rounded-xl px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-[#8259EF]/60 resize-none"
          placeholder="Task payload…"
        />

        {/* Budget + Submit */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-[#0d0d1a] border border-[#1e1e3f] rounded-xl px-3 py-2 flex-1">
            <span className="text-[#8259EF] text-sm">ℏ</span>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              step="0.1"
              min="0.1"
              className="bg-transparent text-sm text-white w-full focus:outline-none"
              placeholder="Budget (HBAR)"
            />
          </div>
          <button
            onClick={submit}
            disabled={loading || !payload.trim()}
            className="btn-primary flex-1"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Executing…
              </span>
            ) : (
              "Submit Task →"
            )}
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className={`mt-4 p-3 rounded-xl border text-xs animate-fade-in ${
          result.status === "completed"
            ? "bg-green-900/20 border-green-500/30"
            : "bg-red-900/20 border-red-500/30"
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`font-semibold ${result.status === "completed" ? "text-green-400" : "text-red-400"}`}>
              {result.status === "completed" ? "✅ Completed" : "❌ Failed"}
            </span>
            {result.cost_hbar !== undefined && (
              <span className="text-[#8259EF]">Cost: {result.cost_hbar} ℏ</span>
            )}
            {result.duration_ms !== undefined && (
              <span className="text-gray-500">{result.duration_ms}ms</span>
            )}
          </div>
          {result.result && (
            <div className="text-gray-300 whitespace-pre-wrap leading-relaxed">
              {result.result}
            </div>
          )}
          {result.error && (
            <div className="text-red-400">{result.error}</div>
          )}
          <div className="text-gray-600 mt-1 font-mono">ID: {result.task_id}</div>
        </div>
      )}
    </div>
  );
}
