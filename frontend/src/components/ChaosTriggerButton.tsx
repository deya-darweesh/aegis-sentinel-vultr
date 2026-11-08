import React from "react";

interface ChaosTriggerButtonProps {
  onTriggerChaos: () => void;
  onTriggerDuel: (preset: string) => void;
  disabled: boolean;
}

export const ChaosTriggerButton: React.FC<ChaosTriggerButtonProps> = ({
  onTriggerChaos,
  onTriggerDuel,
  disabled,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Preset 1: Supply Chain */}
      <button
        onClick={() => onTriggerDuel("SUPPLY_CHAIN_BACKDOOR")}
        disabled={disabled}
        className="px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono font-medium transition disabled:opacity-50"
      >
        <span className="text-cyan-400 font-bold">PRESET 1:</span> Supply-Chain Backdoor
      </button>

      {/* Preset 2: Resource Bomb */}
      <button
        onClick={() => onTriggerDuel("FORK_MEMORY_EXHAUSTION")}
        disabled={disabled}
        className="px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono font-medium transition disabled:opacity-50"
      >
        <span className="text-indigo-400 font-bold">PRESET 2:</span> Fork &amp; Memory Bomb
      </button>

      {/* Preset 3: Financial Invariant */}
      <button
        onClick={() => onTriggerDuel("FINANCIAL_INVARIANT_TAMPER")}
        disabled={disabled}
        className="px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono font-medium transition disabled:opacity-50"
      >
        <span className="text-amber-400 font-bold">PRESET 3:</span> Financial Invariant
      </button>

      {/* Mandatory 1-Click Judge Chaos Detonator */}
      <button
        onClick={onTriggerChaos}
        disabled={disabled}
        className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-500 hover:to-red-600 text-white text-xs font-mono font-bold shadow-lg shadow-rose-950/50 transition-all flex items-center gap-2 disabled:opacity-50"
      >
        <span className="animate-ping w-2 h-2 rounded-full bg-white" />
        DETONATE 1-CLICK CHAOS PROBE
      </button>
    </div>
  );
};
