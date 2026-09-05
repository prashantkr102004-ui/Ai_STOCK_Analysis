import React from "react";
import { Circle, ShieldCheck } from "lucide-react";

export default function Navbar({ health }) {
  const online = health?.status === "healthy";
  return (
    <header className="navbar">
      <div className="brand">
        <ShieldCheck size={24} />
        <div>
          <h1>AI MarketGuard</h1>
          <span>AI-powered stock market intelligence</span>
        </div>
      </div>
      <span className={`statusBadge ${online ? "online" : "offline"}`}>
        <Circle size={10} fill="currentColor" />
        {online ? "Backend Online" : "Backend Offline"}
      </span>
    </header>
  );
}
