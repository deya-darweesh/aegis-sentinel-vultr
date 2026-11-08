import React, { useState } from "react";

interface MultiModalPanelProps {
  onVoiceDetonate: (text: string) => void;
  threatDiagramUrl?: string;
  onGenerateDiagram: (prompt: string) => void;
  onPlayVoiceAlert: (text: string) => void;
}

export const MultiModalPanel: React.FC<MultiModalPanelProps> = ({
  onVoiceDetonate,
  threatDiagramUrl,
  onGenerateDiagram,
  onPlayVoiceAlert,
}) => {
  const [voiceText, setVoiceText] = useState("Detonate memory bomb on payment gateway");
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlayAlert = async () => {
    setIsPlaying(true);
    await onPlayVoiceAlert("Alert: Containment violation intercepted. System immune.");
    setIsPlaying(false);
  };

  return (
    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[11px] flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          Multi-Modal Intelligence Center (Vultr Serverless Inference)
        </h4>
        <span className="text-[10px] text-slate-500">whisper / qwen-tts / z-image</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Audio STT & TTS */}
        <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
          <span className="text-slate-400 font-semibold block text-[11px]">
            1. Voice Incident Detonation (whisper-large-v3)
          </span>
          <input
            type="text"
            value={voiceText}
            onChange={(e) => setVoiceText(e.target.value)}
            className="w-full px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
          />
          <div className="flex gap-2">
            <button
              onClick={() => onVoiceDetonate(voiceText)}
              className="px-3 py-1.5 rounded bg-cyan-900/80 hover:bg-cyan-800 text-cyan-300 border border-cyan-700 text-xs font-bold transition"
            >
              Detonate Spoken Vector
            </button>
            <button
              onClick={handlePlayAlert}
              disabled={isPlaying}
              className="px-3 py-1.5 rounded bg-indigo-900/80 hover:bg-indigo-800 text-indigo-300 border border-indigo-700 text-xs font-bold transition flex items-center gap-1.5"
            >
              <span>{isPlaying ? "Playing..." : "Play Vocal Alert (qwen-tts)"}</span>
            </button>
          </div>
        </div>

        {/* Threat Diagram Generator */}
        <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
          <span className="text-slate-400 font-semibold block text-[11px]">
            2. Threat Topology Visualization (z-image-turbo)
          </span>
          <button
            onClick={() => onGenerateDiagram("AegisSentinel attack topology diagram")}
            className="w-full px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 text-xs font-bold transition"
          >
            Render Attack Topology Diagram
          </button>
          {threatDiagramUrl && (
            <div className="mt-2 rounded border border-slate-800 overflow-hidden bg-black/80 max-h-40 flex items-center justify-center">
              <img src={threatDiagramUrl} alt="Threat Diagram" className="max-h-36 object-contain" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
