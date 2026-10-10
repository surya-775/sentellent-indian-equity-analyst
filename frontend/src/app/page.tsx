"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import StockWatchlist from "@/components/StockWatchlist";
import PersonaCard from "@/components/PersonaCard";
import ChatInterface from "@/components/ChatInterface";
import { StockData, PersonaData, fetchStocks, fetchPersona } from "@/lib/api";

export default function DashboardPage() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [persona, setPersona] = useState<PersonaData | null>(null);
  const [stocksLoading, setStocksLoading] = useState(true);
  const [personaLoading, setPersonaLoading] = useState(true);

  const loadData = async () => {
    try {
      setStocksLoading(true);
      const data = await fetchStocks();
      setStocks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setStocksLoading(false);
    }
  };

  const loadPersonaData = async () => {
    try {
      setPersonaLoading(true);
      const data = await fetchPersona();
      setPersona(data);
    } catch (err) {
      console.error(err);
    } finally {
      setPersonaLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    loadPersonaData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Persona Memory Card & Stock Watchlist */}
          <div className="lg:col-span-5 space-y-6">
            <PersonaCard persona={persona} loading={personaLoading} />
            <StockWatchlist
              stocks={stocks}
              loading={stocksLoading}
              onRefresh={loadData}
            />
          </div>

          {/* Right Column: Chat Interface with Citations */}
          <div className="lg:col-span-7">
            <ChatInterface onPersonaUpdated={loadPersonaData} />
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        <p>Sentellent Full Stack AI SDE Internship Challenge • Deployed on AWS ECS Fargate + RDS PostgreSQL (pgvector)</p>
      </footer>
    </div>
  );
}
