import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisSentinel: Autonomous Cyber Arena",
  description:
    "Autonomous Cyber Shield & Proof-Carrying Immunity Engine for Vultr Agent Rush Hackathon 2026",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#070b14] text-slate-100 antialiased font-sans min-h-screen selection:bg-cyan-500 selection:text-black">
        {children}
      </body>
    </html>
  );
}
