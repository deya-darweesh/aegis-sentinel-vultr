import React, { useEffect, useRef } from "react";

interface DuelTerminalProps {
  logs: Array<{ text: string; stream: "stdout" | "stderr" | "status" | "containment" }>;
  isStreaming: boolean;
}

export const DuelTerminal: React.FC<DuelTerminalProps> = ({ logs, isStreaming }) => {
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="flex flex-col rounded-xl bg-slate-950 border border-slate-800 shadow-2xl overflow-hidden font-mono text-xs">
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500/80" />
          <div className="w-3 h-3 rounded-full bg-amber-500/80" />
          <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          <span className="ml-2 text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
            Quarantine Container Terminal (gVisor runsc)
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <span className="flex items-center gap-1.5 text-cyan-400 text-[10px] animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              LIVE TELEMETRY STREAM
            </span>
          )}
        </div>
      </div>

      <div ref={terminalRef} className="p-4 h-72 overflow-y-auto space-y-1 bg-black/90 text-slate-200">
        {logs.length === 0 ? (
          <div className="text-slate-600 italic">Sandbox quiescent. Select a scenario or detonate chaos test...</div>
        ) : (
          logs.map((log, index) => {
            let color = "text-slate-300";
            if (log.stream === "stderr") color = "text-rose-400 font-semibold";
            if (log.stream === "status") color = "text-cyan-400 font-semibold";
            if (log.stream === "containment") color = "text-emerald-400 font-bold bg-emerald-950/40 p-1 rounded";

            return (
              <div key={index} className={`whitespace-pre-wrap ${color}`}>
                {log.text}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
