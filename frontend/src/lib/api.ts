export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
    ? "/api"
    : "http://localhost:8000/api");

export interface StockData {
  ticker: string;
  name: string;
  exchange: string;
  current_price_inr: number;
  market_cap_crores_inr: number;
  pe_ratio: number | null;
  debt_to_equity: number | null;
  dividend_yield_pct: number | null;
  roce_pct: number | null;
  roe_pct: number | null;
  rolling_sentiment: number;
  sentiment_label: string;
  last_ingested_at: string;
}

export interface PersonaData {
  risk_tolerance: string;
  investment_style: string;
  max_debt_to_equity: number;
  min_dividend_yield: number;
  preferred_sectors: string[];
  excluded_sectors: string[];
  learned_rules: string[];
  updated_at?: string;
}

export interface Citation {
  title: string;
  url: string;
  source: string;
  type?: string;
}

export interface ChatMessageItem {
  id?: number;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp?: string;
}

export async function fetchStocks(): Promise<StockData[]> {
  try {
    const res = await fetch(`${API_BASE}/stocks`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch stocks");
    return await res.json();
  } catch (err) {
    console.warn("Fallback to initial stock data:", err);
    return [
      {
        ticker: "RELIANCE",
        name: "Reliance Industries Ltd",
        exchange: "NSE",
        current_price_inr: 2980.5,
        market_cap_crores_inr: 2015000,
        pe_ratio: 27.4,
        debt_to_equity: 0.42,
        dividend_yield_pct: 0.35,
        roce_pct: 9.8,
        roe_pct: 9.2,
        rolling_sentiment: 0.45,
        sentiment_label: "Bullish",
        last_ingested_at: new Date().toISOString()
      },
      {
        ticker: "TCS",
        name: "Tata Consultancy Services Ltd",
        exchange: "NSE",
        current_price_inr: 4120.0,
        market_cap_crores_inr: 1490000,
        pe_ratio: 30.5,
        debt_to_equity: 0.08,
        dividend_yield_pct: 1.75,
        roce_pct: 58.2,
        roe_pct: 51.4,
        rolling_sentiment: 0.65,
        sentiment_label: "Bullish",
        last_ingested_at: new Date().toISOString()
      },
      {
        ticker: "HDFCBANK",
        name: "HDFC Bank Ltd",
        exchange: "NSE",
        current_price_inr: 1640.25,
        market_cap_crores_inr: 1250000,
        pe_ratio: 19.8,
        debt_to_equity: 0.85,
        dividend_yield_pct: 1.15,
        roce_pct: 16.5,
        roe_pct: 17.1,
        rolling_sentiment: 0.35,
        sentiment_label: "Bullish",
        last_ingested_at: new Date().toISOString()
      },
      {
        ticker: "INFY",
        name: "Infosys Ltd",
        exchange: "NSE",
        current_price_inr: 1890.1,
        market_cap_crores_inr: 785000,
        pe_ratio: 26.2,
        debt_to_equity: 0.11,
        dividend_yield_pct: 2.1,
        roce_pct: 40.5,
        roe_pct: 32.1,
        rolling_sentiment: 0.5,
        sentiment_label: "Bullish",
        last_ingested_at: new Date().toISOString()
      }
    ];
  }
}

export async function followStock(ticker: string): Promise<any> {
  const res = await fetch(`${API_BASE}/stocks/follow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker })
  });
  if (!res.ok) throw new Error("Failed to follow/ingest ticker");
  return await res.json();
}

export async function fetchPersona(): Promise<PersonaData> {
  try {
    const res = await fetch(`${API_BASE}/persona`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch persona");
    return await res.json();
  } catch (err) {
    return {
      risk_tolerance: "Conservative",
      investment_style: "Dividend & Income",
      max_debt_to_equity: 0.5,
      min_dividend_yield: 1.5,
      preferred_sectors: ["Information Technology", "FMCG"],
      excluded_sectors: [],
      learned_rules: [
        "Avoid high-debt companies (D/E > 0.5)",
        "Focus on regular dividend yield (>1.5%)"
      ]
    };
  }
}

export async function sendMessage(message: string, sessionId: string = "default"): Promise<{ reply: string; citations: Citation[] }> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  if (!res.ok) throw new Error("Failed to send message to Agent");
  return await res.json();
}
