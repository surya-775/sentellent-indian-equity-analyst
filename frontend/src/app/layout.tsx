import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sentellent Indian-Equity Analyst (RAG)",
  description: "Personal Agentic AI Indian-Equity Analyst (NSE / BSE) with LangGraph & pgvector",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
