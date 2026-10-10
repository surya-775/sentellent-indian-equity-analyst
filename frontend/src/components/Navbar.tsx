"use client";

import React, { useEffect, useState, useRef } from "react";
import { TrendingUp, User, LogOut, CheckCircle2 } from "lucide-react";

declare global {
  interface Window {
    google?: any;
  }
}

interface UserProfile {
  name: string;
  email: string;
  avatar_url?: string;
}

export default function Navbar() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const googleBtnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Check saved session
    const savedUser = localStorage.getItem("sentellent_user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {}
    }

    // Initialize Google Identity Services
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (typeof window !== "undefined" && window.google && clientId) {
      try {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleCredentialResponse,
        });

        if (googleBtnRef.current && !user) {
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: "filled_blue",
            size: "medium",
            shape: "pill",
            text: "signin_with",
          });
        }
      } catch (err) {
        console.warn("Google Auth Init:", err);
      }
    }
  }, [user]);

  const handleGoogleCredentialResponse = async (response: any) => {
    try {
      const res = await fetch("http://localhost:8000/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: response.credential }),
      });
      if (res.ok) {
        const data = await res.json();
        const profile: UserProfile = {
          name: data.user.name,
          email: data.user.email,
          avatar_url: data.user.avatar_url,
        };
        setUser(profile);
        localStorage.setItem("sentellent_user", JSON.stringify(profile));
        localStorage.setItem("sentellent_token", data.access_token);
      }
    } catch (e) {
      console.error("Auth error:", e);
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("sentellent_user");
    localStorage.removeItem("sentellent_token");
    window.location.reload();
  };

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
          <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>NSE / BSE Feeds Active</span>
          </div>

          {user ? (
            <div className="flex items-center space-x-3 bg-slate-800/80 border border-slate-700/80 px-3 py-1.5 rounded-xl text-xs">
              {user.avatar_url ? (
                <img src={user.avatar_url} alt={user.name} className="h-6 w-6 rounded-full" />
              ) : (
                <div className="h-6 w-6 rounded-full bg-emerald-600 flex items-center justify-center text-white">
                  <User className="h-3.5 w-3.5" />
                </div>
              )}
              <div className="hidden md:block text-left">
                <span className="font-medium text-slate-100 block leading-tight">{user.name}</span>
                <span className="text-[10px] text-slate-400">{user.email}</span>
              </div>
              <button
                onClick={handleLogout}
                className="text-slate-400 hover:text-rose-400 ml-1 p-1"
                title="Sign Out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <div ref={googleBtnRef}></div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
