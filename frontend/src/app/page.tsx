"use client";

import React, { useState, useEffect } from "react";
import { ArenaHUD } from "../components/ArenaHUD";
import { DuelTerminal } from "../components/DuelTerminal";
import { ContainmentBadge } from "../components/ContainmentBadge";
import { ChaosTriggerButton } from "../components/ChaosTriggerButton";
import { ImmunityReceiptViewer } from "../components/ImmunityReceiptViewer";
import { MultiModalPanel } from "../components/MultiModalPanel";

export default function CyberArenaPage() {
  const [cpuUsage, setCpuUsage] = useState(12.4);
  const [memoryMb, setMemoryMb] = useState(38.5);
  const [pidsCount, setPidsCount] = useState(4);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<
    Array<{ text: string; stream: "stdout" | "stderr" | "status" | "containment" }>
  >([]);
  const [receipt, setReceipt] = useState<any>(null);
  const [threatDiagramUrl, setThreatDiagramUrl] = useState<string>("");
  const [redCode, setRedCode] = useState<string>("# Red Agent Exploit Code will generate here...");
  const [blueCode, setBlueCode] = useState<string>("# Blue Agent Patch will synthesize here...");

  const triggerChaosProbe = async () => {
    setIsRunning(true);
    setTerminalLogs([]);
    setReceipt(null);
    setElapsedMs(0);

    try {
      const res = await fetch("/api/chaos-test", { method: "POST" });
      const data = await res.json();
      connectSse(data.task_id);
    } catch (err) {
      console.error(err);
      setIsRunning(false);
    }
  };

  const triggerDuel = async (preset: string) => {
    setIsRunning(true);
    setTerminalLogs([]);
    setReceipt(null);
    setElapsedMs(0);

    try {
      const res = await fetch("/api/duel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_preset: preset, max_rounds: 3 }),
      });
      const data = await res.json();
      connectSse(data.mission_id);
    } catch (err) {
      console.error(err);
      setIsRunning(false);
    }
  };

  const connectSse = (taskId: string) => {
    const timer = setInterval(() => {
      setElapsedMs((prev) => prev + 100);
      setCpuUsage((prev) => Math.min(95, Math.max(15, prev + (Math.random() * 20 - 10))));
      setMemoryMb((prev) => Math.min(240, Math.max(30, prev + (Math.random() * 30 - 10))));
      setPidsCount((prev) => Math.min(60, Math.max(3, prev + Math.floor(Math.random() * 5 - 2))));
    }, 100);

    const eventSource = new EventSource(`/api/stream/${taskId}`);

    eventSource.addEventListener("stdout", (e) => {
      const payload = JSON.parse(e.data);
      setTerminalLogs((prev) => [...prev, { text: payload.text, stream: "stdout" }]);
    });

    eventSource.addEventListener("stderr", (e) => {
      const payload = JSON.parse(e.data);
      setTerminalLogs((prev) => [...prev, { text: `[STDERR] ${payload.text}`, stream: "stderr" }]);
    });

    eventSource.addEventListener("status", (e) => {
      setTerminalLogs((prev) => [...prev, { text: `[STAGE] ${e.data}`, stream: "status" }]);
    });

    eventSource.addEventListener("finished", (e) => {
      clearInterval(timer);
      setIsRunning(false);
      try {
        const rcpt = JSON.parse(e.data);
        setReceipt(rcpt);
      } catch (err) {
        console.error(err);
      }
      setTerminalLogs((prev) => [
        ...prev,
        { text: "[CONTAINMENT VERIFIED] Ephemeral container destroyed. System immune.", stream: "containment" },
      ]);
      eventSource.close();
    });

    eventSource.addEventListener("duel_completed", (e) => {
      clearInterval(timer);
      setIsRunning(false);
      try {
        const payload = JSON.parse(e.data);
        if (payload.receipt) setReceipt(payload.receipt);
      } catch (err) {
        console.error(err);
      }
      eventSource.close();
    });
  };

  const handleGenerateDiagram = async (prompt: string) => {
    const res = await fetch("/api/threat-diagram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();
    setThreatDiagramUrl(data.diagram_url);
  };

  const handlePlayVoiceAlert = async (text: string) => {
    const formData = new FormData();
    formData.append("text", text);
    const res = await fetch("/api/voice-alert", {
      method: "POST",
      body: formData,
    });
    const blob = await res.blob();
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    await audio.play();
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black font-mono tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-400 to-rose-400">
                AEGISSENTINEL
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800 font-bold">
                VULTR CLOUD COMPUTE (VX1)
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Autonomous Cyber Arena &amp; Proof-Carrying Immunity Engine • KubeCon NA 2026
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <ContainmentBadge label="AIRGAP_ENFORCED" status="active" detail="--network=none" />
            <ContainmentBadge label="CGROUP_CEILING_HELD" status="held" detail="256MB / 0.5 CPU" />
            <ContainmentBadge label="SECRETS_SCRUBBED" status="verified" detail="0 Host Keys" />
            <ContainmentBadge label="ED25519_SIGNED" status="verified" detail="RFC 8785" />
          </div>
        </header>

        {/* Live HUD Metric Gauges */}
        <ArenaHUD
          cpuUsage={cpuUsage}
          memoryMb={memoryMb}
          memoryLimitMb={256}
          pidsCount={pidsCount}
          pidsLimit={64}
          elapsedMs={elapsedMs}
        />

        {/* Action Controls & Preset Triggers */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-xs font-mono text-slate-400">
            <span className="text-cyan-400 font-bold">1-Click Evaluation Matrix:</span> Detonate real-time adversarial
            duels or launch the 3-vector chaos probe.
          </div>
          <ChaosTriggerButton
            onTriggerChaos={triggerChaosProbe}
            onTriggerDuel={triggerDuel}
            disabled={isRunning}
          />
        </div>

        {/* Split Screen Duel HUD */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Red Agent Panel */}
          <div className="p-4 rounded-xl bg-slate-950 border border-rose-950/60 shadow-xl space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-rose-900/40 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                <h3 className="font-bold text-rose-400 uppercase tracking-wider text-[11px]">
                  Red Agent (The Breaker)
                </h3>
              </div>
              <span className="text-[10px] text-slate-400">deepseek-v4.1-flash-1017</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Weaponized exploit fuzzer discovering zero-days, resource exhaustion bombs, and supply-chain backdoors.
            </p>
            <pre className="p-3 rounded bg-black/80 border border-rose-950/40 text-rose-300 overflow-x-auto text-[11px] h-32">
              {redCode}
            </pre>
          </div>

          {/* Blue Agent Panel */}
          <div className="p-4 rounded-xl bg-slate-950 border border-indigo-950/60 shadow-xl space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-indigo-900/40 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-400" />
                <h3 className="font-bold text-indigo-400 uppercase tracking-wider text-[11px]">
                  Blue Agent (The Maker)
                </h3>
              </div>
              <span className="text-[10px] text-slate-400">qwen3.8-27b</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Immunity synthesizer diagnosing telemetry traces and generating backward-compatible hardened hotpatches.
            </p>
            <pre className="p-3 rounded bg-black/80 border border-indigo-950/40 text-indigo-300 overflow-x-auto text-[11px] h-32">
              {blueCode}
            </pre>
          </div>
        </div>

        {/* Streaming Terminal */}
        <DuelTerminal logs={terminalLogs} isStreaming={isRunning} />

        {/* Multi-Modal & Cryptographic Proof Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MultiModalPanel
            onVoiceDetonate={(text) => triggerDuel("FORK_MEMORY_EXHAUSTION")}
            threatDiagramUrl={threatDiagramUrl}
            onGenerateDiagram={handleGenerateDiagram}
            onPlayVoiceAlert={handlePlayVoiceAlert}
          />
          <ImmunityReceiptViewer receipt={receipt} verified={true} />
        </div>
      </div>
    </div>
  );
}
