import React from "react";

interface ContainmentBadgeProps {
  label: string;
  status: "active" | "held" | "blocked" | "verified";
  detail?: string;
}

export const ContainmentBadge: React.FC<ContainmentBadgeProps> = ({ label, status, detail }) => {
  const colorMap = {
    active: "bg-cyan-950/80 text-cyan-400 border-cyan-800",
    held: "bg-emerald-950/80 text-emerald-400 border-emerald-800",
    blocked: "bg-rose-950/80 text-rose-400 border-rose-800",
    verified: "bg-indigo-950/80 text-indigo-400 border-indigo-800",
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-mono font-medium ${colorMap[status]}`}>
      <span className="w-2 h-2 rounded-full animate-pulse bg-current" />
      <span>{label}</span>
      {detail && <span className="opacity-70 text-[10px]">({detail})</span>}
    </div>
  );
};
