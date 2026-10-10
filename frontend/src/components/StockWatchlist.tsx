"use client";

import React, { useState } from "react";
import { Plus, RefreshCw, TrendingUp, TrendingDown, Minus, Building2, AlertCircle } from "lucide-react";
import { StockData, followStock } from "@/lib/api";

interface StockWatchlistProps {
  stocks: StockData[];
  loading: boolean;
  onRefresh: () => void;
}

export default function StockWatchlist({ stocks, loading, onRefresh }: StockWatchlistProps) {
  const [tickerInput, setTickerInput] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleFollow = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = tickerInput.trim().toUpperCase();
    if (!clean) return;

    setIngesting(true);
    setStatusMsg(`Ingesting fundamentals & news for ${clean}...`);
    try {
      await followStock(clean);
      setStatusMsg(`Successfully indexed ${clean}!`);
      setTickerInput("");
      onRefresh();
      setTimeout(() => setStatusMsg(null), 4000);
    } catch (err: any) {
      setStatusMsg(`Ingestion failed: ${err.message}`);
    } finally {
      setIngesting(false);
    }
  };

  const getSentimentBadge = (label: string, score: number) => {
    if (label === "Bullish" || score > 0.2) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <TrendingUp className="h-3 w-3" />
          Bullish ({score > 0 ? `+${score}` : score})
        </span>
      );
    } else if (label === "Bearish" || score < -0.2) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <TrendingDown className="h-3 w-3" />
          Bearish ({score})
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <Minus className="h-3 w-3" />
        Neutral ({score})
      </span>
    );
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100 text-sm">Followed Indian Equities</h3>
            <p className="text-xs text-slate-400">Live NSE/BSE fundamentals & vector-indexed news</p>
          </div>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all disabled:opacity-50"
          title="Refresh stocks"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Follow / Ingest Input */}
      <form onSubmit={handleFollow} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={tickerInput}
            onChange={(e) => setTickerInput(e.target.value)}
            placeholder="Follow NSE/BSE Ticker (e.g. ITC, TATAMOTORS)"
            className="flex-1 bg-slate-950/80 border border-slate-800 focus:border-emerald-500 rounded-xl px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all"
          />
          <button
            type="submit"
            disabled={ingesting || !tickerInput.trim()}
            className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-medium px-4 py-2 rounded-xl text-sm transition-all shadow-lg shadow-emerald-600/20 disabled:shadow-none disabled:text-slate-500 cursor-pointer disabled:cursor-not-allowed"
          >
            {ingesting ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            <span>Ingest</span>
          </button>
        </div>
        {statusMsg && (
          <p className="text-xs mt-2 text-emerald-400 flex items-center gap-1.5">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>{statusMsg}</span>
          </p>
        )}
      </form>

      {/* Stocks Cards Grid */}
      <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
        {stocks.map((stock) => (
          <div
            key={stock.ticker}
            className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-100 text-sm tracking-wide">{stock.ticker}</span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    {stock.exchange}
                  </span>
                </div>
                <p className="text-xs text-slate-400 truncate max-w-[200px]">{stock.name}</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-semibold text-white">
                  ₹{stock.current_price_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
                <div className="mt-1">
                  {getSentimentBadge(stock.sentiment_label, stock.rolling_sentiment)}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-900/90 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px]">Market Cap</span>
                <span className="text-slate-300 font-medium">₹{Math.round(stock.market_cap_crores_inr).toLocaleString("en-IN")} Cr</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">P/E</span>
                <span className="text-slate-300 font-medium">{stock.pe_ratio ?? "N/A"}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">D/E Ratio</span>
                <span className={`font-medium ${stock.debt_to_equity && stock.debt_to_equity > 1 ? "text-amber-400" : "text-emerald-400"}`}>
                  {stock.debt_to_equity ?? "N/A"}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Div Yield</span>
                <span className="text-slate-300 font-medium">{stock.dividend_yield_pct ? `${stock.dividend_yield_pct}%` : "0%"}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
