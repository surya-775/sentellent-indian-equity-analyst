"use client";

import React from "react";
import { Brain, Shield, Percent, DollarSign, BookOpen, Sparkles } from "lucide-react";
import { PersonaData } from "@/lib/api";

interface PersonaCardProps {
  persona: PersonaData | null;
  loading: boolean;
}

export default function PersonaCard({ persona, loading }: PersonaCardProps) {
  if (loading || !persona) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 animate-pulse">
        <div className="h-5 bg-slate-800 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-slate-800/60 rounded w-full"></div>
          <div className="h-4 bg-slate-800/60 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/70 border border-slate-800 hover:border-slate-700/80 transition-all rounded-2xl p-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100 text-sm">Investor Persona & Memory Graph</h3>
            <p className="text-xs text-slate-400">Dynamic agentic profile (updated from chat & ingest)</p>
          </div>
        </div>
        <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 flex items-center gap-1">
          <Sparkles className="h-2.5 w-2.5" />
          pgvector Synced
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-950/50 border border-slate-800/70 p-3 rounded-xl">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
            <Shield className="h-3.5 w-3.5 text-emerald-400" />
            <span>Risk Appetite</span>
          </div>
          <p className="text-sm font-semibold text-slate-100">{persona.risk_tolerance}</p>
        </div>

        <div className="bg-slate-950/50 border border-slate-800/70 p-3 rounded-xl">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
            <DollarSign className="h-3.5 w-3.5 text-blue-400" />
            <span>Style</span>
          </div>
          <p className="text-sm font-semibold text-slate-100">{persona.investment_style}</p>
        </div>

        <div className="bg-slate-950/50 border border-slate-800/70 p-3 rounded-xl">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
            <Percent className="h-3.5 w-3.5 text-amber-400" />
            <span>Max Debt-to-Equity</span>
          </div>
          <p className="text-sm font-semibold text-slate-100">{persona.max_debt_to_equity}</p>
        </div>

        <div className="bg-slate-950/50 border border-slate-800/70 p-3 rounded-xl">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
            <Percent className="h-3.5 w-3.5 text-teal-400" />
            <span>Min Dividend Yield</span>
          </div>
          <p className="text-sm font-semibold text-slate-100">{persona.min_dividend_yield}%</p>
        </div>
      </div>

      {persona.learned_rules && persona.learned_rules.length > 0 && (
        <div className="bg-slate-950/40 border border-slate-800/60 p-3 rounded-xl">
          <div className="flex items-center space-x-1.5 text-xs font-medium text-slate-300 mb-2">
            <BookOpen className="h-3.5 w-3.5 text-purple-400" />
            <span>Learned Persona Constraints (Hard Filters):</span>
          </div>
          <ul className="space-y-1.5">
            {persona.learned_rules.map((rule, idx) => (
              <li key={idx} className="text-xs text-slate-300 flex items-start space-x-2">
                <span className="h-1.5 w-1.5 rounded-full bg-purple-400 mt-1.5 shrink-0" />
                <span>{rule}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
