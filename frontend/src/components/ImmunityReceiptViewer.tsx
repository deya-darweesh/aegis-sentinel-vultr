import React from "react";

export interface ImmunityReceipt {
  receipt_id: string;
  timestamp: string;
  task_slug: string;
  status: string;
  exit_code: number;
  duration_ms: number;
  memory_peak_mb: number;
  runtime_engine: string;
  container_id: string;
  digest_sha256: string;
  ed25519_signature: string;
  public_key: string;
  violation?: string;
}

interface ImmunityReceiptViewerProps {
  receipt: ImmunityReceipt | null;
  onVerify?: () => void;
  verified?: boolean;
}

export const ImmunityReceiptViewer: React.FC<ImmunityReceiptViewerProps> = ({
  receipt,
  onVerify,
  verified = true,
}) => {
  if (!receipt) {
    return (
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono text-xs text-slate-500">
        No cryptographic immunity certificate issued yet. Execute a duel or chaos probe.
      </div>
    );
  }

  return (
    <div className="p-5 rounded-xl bg-slate-950 border border-emerald-900/50 shadow-2xl font-mono text-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-400" />
          <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider">
            Proof of Verified Immunity Certificate
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[11px] font-bold">
            ED25519 VERIFIED
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-slate-300">
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Receipt ID</span>
          <span className="text-cyan-400 font-bold">{receipt.receipt_id}</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Verification Status</span>
          <span className="text-emerald-400 font-bold">{receipt.status}</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Exit Code</span>
          <span className="text-slate-200">{receipt.exit_code} (Deterministic Truth)</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Runtime Engine</span>
          <span className="text-slate-200">{receipt.runtime_engine} (Isolation Kernel)</span>
        </div>
        <div className="col-span-1 md:col-span-2">
          <span className="text-slate-500 block text-[10px] uppercase">Canonical SHA-256 Digest</span>
          <span className="text-slate-400 text-[11px] break-all">{receipt.digest_sha256}</span>
        </div>
        <div className="col-span-1 md:col-span-2">
          <span className="text-slate-500 block text-[10px] uppercase">Ed25519 Digital Signature</span>
          <span className="text-amber-400 text-[11px] break-all">{receipt.ed25519_signature}</span>
        </div>
        <div className="col-span-1 md:col-span-2">
          <span className="text-slate-500 block text-[10px] uppercase">Signer Public Key</span>
          <span className="text-indigo-400 text-[11px] break-all">{receipt.public_key}</span>
        </div>
      </div>
    </div>
  );
};
