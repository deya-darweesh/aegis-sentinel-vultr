import React from "react";

interface ArenaHUDProps {
  cpuUsage: number;
  memoryMb: number;
  memoryLimitMb: number;
  pidsCount: number;
  pidsLimit: number;
  elapsedMs: number;
}

export const ArenaHUD: React.FC<ArenaHUDProps> = ({
  cpuUsage,
  memoryMb,
  memoryLimitMb,
  pidsCount,
  pidsLimit,
  elapsedMs,
}) => {
  const memPercent = Math.min(100, Math.round((memoryMb / memoryLimitMb) * 100));
  const pidPercent = Math.min(100, Math.round((pidsCount / pidsLimit) * 100));

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-2xl">
      {/* CPU Gauge */}
      <div className="flex flex-col gap-1 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400">vCPU Allocation</span>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold font-mono text-cyan-400">{cpuUsage}%</span>
          <span className="text-xs text-slate-500 font-mono">0.5 Cores</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div className="bg-cyan-500 h-1.5 transition-all duration-300" style={{ width: `${cpuUsage}%` }} />
        </div>
      </div>

      {/* Memory Gauge */}
      <div className="flex flex-col gap-1 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400">cgroup RAM Ceiling</span>
        <div className="flex items-baseline justify-between">
          <span className={`text-2xl font-bold font-mono ${memPercent > 80 ? "text-rose-400" : "text-emerald-400"}`}>
            {memoryMb.toFixed(1)} <span className="text-sm">MB</span>
          </span>
          <span className="text-xs text-slate-500 font-mono">/ {memoryLimitMb}MB</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-1.5 transition-all duration-300 ${memPercent > 80 ? "bg-rose-500" : "bg-emerald-500"}`}
            style={{ width: `${memPercent}%` }}
          />
        </div>
      </div>

      {/* PIDs Gauge */}
      <div className="flex flex-col gap-1 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Fork Bomb Throttle</span>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold font-mono text-indigo-400">{pidsCount} PIDs</span>
          <span className="text-xs text-slate-500 font-mono">Limit: {pidsLimit}</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div className="bg-indigo-500 h-1.5 transition-all duration-300" style={{ width: `${pidPercent}%` }} />
        </div>
      </div>

      {/* Execution Timer */}
      <div className="flex flex-col gap-1 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Wall-Clock Timer</span>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold font-mono text-amber-400">{(elapsedMs / 1000).toFixed(2)}s</span>
          <span className="text-xs text-slate-500 font-mono">Ceiling: 12.0s</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-amber-500 h-1.5 transition-all duration-300"
            style={{ width: `${Math.min(100, (elapsedMs / 12000) * 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};
