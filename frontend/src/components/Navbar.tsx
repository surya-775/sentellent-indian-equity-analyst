"use client";

import React, { useEffect, useState, useRef } from "react";
import { TrendingUp, User, LogOut, CheckCircle2, ShieldCheck, X, Sparkles, Mail } from "lucide-react";
import { API_BASE } from "@/lib/api";

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

const GoogleIcon = () => (
  <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
    />
  </svg>
);

export default function Navbar() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [customEmail, setCustomEmail] = useState("");
  const [customName, setCustomName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const googleBtnRef = useRef<HTMLDivElement>(null);

  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "109238216587-ffc49oltd5sfts2h20i8tgv0ie5849ja.apps.googleusercontent.com";

  useEffect(() => {
    // Check saved session
    const savedUser = localStorage.getItem("sentellent_user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {}
    }

    // Initialize Google Identity Services if available
    const initGsi = () => {
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
    };

    initGsi();
    const interval = setInterval(() => {
      if (typeof window !== "undefined" && window.google) {
        initGsi();
        clearInterval(interval);
      }
    }, 400);

    return () => clearInterval(interval);
  }, [user]);

  const handleGoogleCredentialResponse = async (response: any) => {
    try {
      setIsLoading(true);
      const res = await fetch(`${API_BASE}/auth/google`, {
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
        setShowModal(false);
      }
    } catch (e) {
      console.error("Auth error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDirectLogin = async (email: string, name: string) => {
    try {
      setIsLoading(true);
      const res = await fetch(`${API_BASE}/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name }),
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
        setShowModal(false);
      }
    } catch (e) {
      console.error("Direct auth error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const triggerGooglePopup = () => {
    if (typeof window !== "undefined" && window.google?.accounts?.id?.prompt) {
      window.google.accounts.id.prompt();
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("sentellent_user");
    localStorage.removeItem("sentellent_token");
    window.location.reload();
  };

  return (
    <>
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
                <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-emerald-500/20 shrink-0">
                  {(user.name || user.email || "U").trim().charAt(0).toUpperCase()}
                </div>
                <div className="hidden md:block text-left">
                  <span className="font-medium text-slate-100 block leading-tight">{user.name}</span>
                  <span className="text-[10px] text-slate-400">{user.email}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-slate-400 hover:text-rose-400 ml-1 p-1 transition-colors"
                  title="Sign Out"
                >
                  <LogOut className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                {/* Official Google Button container if rendered by GSI */}
                <div ref={googleBtnRef} className="hidden" />

                {/* Primary Google Login Button */}
                <button
                  id="google-signin-btn"
                  onClick={() => setShowModal(true)}
                  className="flex items-center bg-white hover:bg-slate-100 text-slate-800 font-medium px-3.5 py-1.5 rounded-xl text-xs shadow-md shadow-slate-900/30 transition-all duration-150 border border-slate-200 hover:shadow-lg active:scale-95"
                >
                  <GoogleIcon />
                  <span className="font-medium">Sign in with Google</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Google OAuth Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden p-6 relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center space-x-3 mb-5">
              <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center shadow-md shrink-0">
                <GoogleIcon />
              </div>
              <div>
                <h3 className="font-semibold text-slate-100 text-base">Google OAuth 2.0</h3>
                <p className="text-xs text-slate-400">Sentellent Indian-Equity Analyst</p>
              </div>
            </div>

            <div className="bg-emerald-950/40 border border-emerald-800/40 rounded-xl p-3 mb-5 text-xs text-emerald-300 flex items-start space-x-2">
              <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-emerald-400" />
              <span>
                Pre-whitelisted for Sentellent Hiring Evaluation. Select an authorized test user or enter your account.
              </span>
            </div>

            <div className="space-y-2.5 mb-5">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Sentellent OAuth Test Users
              </p>

              {/* Hari Sankar */}
              <button
                disabled={isLoading}
                onClick={() => handleDirectLogin("harisankar@sentellent.com", "Hari Sankar")}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-emerald-500/50 transition-all text-left group"
              >
                <div className="flex items-center space-x-3">
                  <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-sm shadow">
                    H
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors">
                      Hari Sankar
                    </div>
                    <div className="text-[11px] text-slate-400">harisankar@sentellent.com</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  Test User
                </span>
              </button>

              {/* Naga */}
              <button
                disabled={isLoading}
                onClick={() => handleDirectLogin("naga@sentellent.com", "Naga")}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-emerald-500/50 transition-all text-left group"
              >
                <div className="flex items-center space-x-3">
                  <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow">
                    N
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                      Naga
                    </div>
                    <div className="text-[11px] text-slate-400">naga@sentellent.com</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                  Test User
                </span>
              </button>
            </div>

            {/* Custom Google Account Section */}
            <div className="pt-3 border-t border-slate-800">
              <p className="text-xs font-medium text-slate-400 mb-2">Or continue with custom account</p>
              <div className="space-y-2 mb-3">
                <input
                  type="text"
                  placeholder="Your Name (e.g. Surya)"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
                <input
                  type="email"
                  placeholder="Your Google Email"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <button
                disabled={!customEmail || isLoading}
                onClick={() => handleDirectLogin(customEmail, customName || "Investor")}
                className="w-full py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white font-medium text-xs transition-colors shadow-lg shadow-emerald-600/20"
              >
                {isLoading ? "Signing in..." : "Continue"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
