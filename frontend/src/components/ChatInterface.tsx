"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, ExternalLink, ShieldCheck, CheckCircle2 } from "lucide-react";
import { ChatMessageItem, sendMessage } from "@/lib/api";

interface ChatInterfaceProps {
  onPersonaUpdated: () => void;
}

const PRESET_PROMPTS = [
  "What's the sentiment on TCS this week?",
  "I'm a conservative, dividend-focused investor and I avoid high-debt companies",
  "What should I buy this week?",
  "What is the sentiment on UNKNOWN_TICKER this week?"
];

export default function ChatInterface({ onPersonaUpdated }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessageItem[]>([
    {
      role: "assistant",
      content:
        "Hello! I am your **Personal Agentic AI Indian-Equity Analyst** for the NSE & BSE. I ingest real-time fundamentals from Screener and Indian financial news into pgvector, learn your investment persona dynamically, and deliver strictly grounded, cited insights in INR.\n\nTry updating your persona or asking for research on followed stocks!",
      citations: []
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    const userMessage: ChatMessageItem = {
      role: "user",
      content: text
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const response = await sendMessage(text);
      const assistantMessage: ChatMessageItem = {
        role: "assistant",
        content: response.reply,
        citations: response.citations
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // If the query was a persona update, notify parent to refresh persona card
      if (
        text.toLowerCase().includes("conservative") ||
        text.toLowerCase().includes("dividend") ||
        text.toLowerCase().includes("avoid") ||
        text.toLowerCase().includes("investor")
      ) {
        onPersonaUpdated();
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error contacting agent service: ${err.message}. Please check that the backend is running.`,
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl flex flex-col h-[740px] shadow-2xl backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-100 text-sm">Agentic Equity Research Chat</h2>
            <p className="text-xs text-slate-400 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              LangGraph RAG • Zero-Hallucination Guardrail Active
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span className="hidden sm:inline">Grounded in INR (₹)</span>
        </div>
      </div>

      {/* Preset Chips */}
      <div className="px-4 py-2 bg-slate-950/40 border-b border-slate-800/60 flex items-center gap-2 overflow-x-auto text-xs">
        <span className="text-slate-500 shrink-0 flex items-center gap-1">
          <Sparkles className="h-3 w-3 text-emerald-400" /> Quick Tests:
        </span>
        {PRESET_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            className="shrink-0 bg-slate-800/80 hover:bg-slate-700 hover:border-slate-600 border border-slate-700/60 text-slate-300 hover:text-white px-2.5 py-1 rounded-full transition-all cursor-pointer text-[11px] disabled:opacity-50"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 ${
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            <div
              className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 ${
                msg.role === "user"
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-800 border border-slate-700 text-emerald-400"
              }`}
            >
              {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>

            <div
              className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-emerald-600 text-white rounded-tr-none shadow-md shadow-emerald-900/30"
                  : "bg-slate-950/70 border border-slate-800 text-slate-200 rounded-tl-none shadow-md"
              }`}
            >
              <div className="whitespace-pre-wrap font-sans text-[13.5px]">
                {msg.content}
              </div>

              {/* Citations Box */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-800/80">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 mb-2">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Grounded Sources & Citations:</span>
                  </div>
                  <div className="space-y-1.5">
                    {msg.citations.map((c, cIdx) => (
                      <a
                        key={cIdx}
                        href={c.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center justify-between p-2 rounded-lg bg-slate-900/80 hover:bg-slate-850 border border-slate-800 text-xs text-slate-300 hover:text-emerald-300 transition-all group"
                      >
                        <span className="truncate pr-2 font-medium">
                          {cIdx + 1}. {c.title}
                        </span>
                        <div className="flex items-center gap-1 text-[10px] text-slate-400 shrink-0 group-hover:text-emerald-400">
                          <span>{c.source}</span>
                          <ExternalLink className="h-3 w-3" />
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="h-8 w-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400">
              <Bot className="h-4 w-4" />
            </div>
            <div className="bg-slate-950/70 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-xs text-slate-400 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <span>LangGraph agent retrieving pgvector articles & screening fundamentals...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Field */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 bg-slate-900/90 border-t border-slate-800 flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask research questions, screen NSE/BSE stocks, or teach your investor persona..."
          disabled={loading}
          className="flex-1 bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-medium p-2.5 px-4 rounded-xl transition-all shadow-lg shadow-emerald-600/20 disabled:shadow-none disabled:text-slate-500 cursor-pointer disabled:cursor-not-allowed flex items-center gap-1.5"
        >
          <Send className="h-4 w-4" />
          <span className="text-sm font-semibold hidden sm:inline">Ask Agent</span>
        </button>
      </form>
    </div>
  );
}
