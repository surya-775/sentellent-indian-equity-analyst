"use client";

import React from "react";
import { TrendingUp, ShieldCheck, Server, UserCheck } from "lucide-react";

export default function Navbar() {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">Sentellent</span>
              <span className="text-xs uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                NSE / BSE RAG Agent
              </span>
            </div>
            <p className="text-xs text-slate-400">Equity Research Chief of Staff</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg text-slate-300">
            <Server className="h-3.5 w-3.5 text-emerald-400" />
            <span>AWS ECS + pgvector Live</span>
          </div>

          <div className="flex items-center space-x-2 text-xs bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-emerald-300">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span className="hidden sm:inline">OAuth Test Users:</span>
            <span className="font-mono text-emerald-200">harisankar@sentellent.com</span>
          </div>
        </div>
      </div>
    </header>
  );
}
