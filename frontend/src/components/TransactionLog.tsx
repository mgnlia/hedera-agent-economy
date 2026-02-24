"use client";

import { Transaction } from "@/app/page";

export function TransactionLog({ transactions }: { transactions: Transaction[] }) {
  const sorted = [...transactions].reverse();

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">💸 Settlement Transactions</h3>
        <span className="text-xs text-gray-500">{transactions.length} total</span>
      </div>

      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
        {sorted.length === 0 ? (
          <div className="text-center py-6 text-gray-500 text-sm">
            No settlements yet — submit a task to trigger payment
          </div>
        ) : (
          sorted.map((tx, i) => (
            <div
              key={tx.tx_id + i}
              className="flex items-center gap-3 p-2.5 rounded-xl bg-[#0d0d1a] border border-[#1e1e3f] animate-fade-in"
            >
              <span className="text-lg">💸</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-gray-400 truncate">{tx.worker_id}</span>
                  <span className="text-xs text-[#8259EF] font-bold ml-auto">
                    +{tx.amount_hbar.toFixed(4)} ℏ
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-gray-600 font-mono truncate">{tx.tx_id}</span>
                  {tx.mock && (
                    <span className="badge bg-yellow-400/10 text-yellow-400 text-xs">MOCK</span>
                  )}
                  <span className="text-xs text-gray-600 ml-auto">{tx.duration_ms}ms</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
