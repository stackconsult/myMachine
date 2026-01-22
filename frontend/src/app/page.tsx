"use client";

import { useState } from "react";
import { AgenticChatInterface } from "@/components/AgenticChatInterface";
import { Brain, Sparkles, Wrench, BarChart3, Users, Mail, Target, Calendar, Settings, TrendingUp } from "lucide-react";

export default function HomePage() {
  const [activeView, setActiveView] = useState<"dashboard" | "chat">("dashboard");

  const layers = [
    { id: "1", name: "Prospect Research", desc: "Find businesses with weak GBP", icon: <Users className="w-5 h-5" /> },
    { id: "2", name: "Pitch Generator", desc: "Personalized outreach content", icon: <Target className="w-5 h-5" /> },
    { id: "3", name: "Outreach Engine", desc: "Multi-channel message delivery", icon: <Mail className="w-5 h-5" /> },
    { id: "4", name: "Booking Handler", desc: "Calendly webhook to CRM", icon: <Calendar className="w-5 h-5" /> },
    { id: "5", name: "Onboarding Flow", desc: "Automated client setup", icon: <Settings className="w-5 h-5" /> },
    { id: "6", name: "GBP Optimizer", desc: "Google Business Profile automation", icon: <BarChart3 className="w-5 h-5" /> },
    { id: "7", name: "Reporting Engine", desc: "Performance analytics with AI", icon: <TrendingUp className="w-5 h-5" /> },
    { id: "8", name: "Finance Tracker", desc: "Revenue and expense tracking", icon: <Wrench className="w-5 h-5" /> },
    { id: "9", name: "Self-Learning", desc: "Feedback loop for improvement", icon: <Brain className="w-5 h-5" /> },
  ];

  if (activeView === "chat") {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1">
          <AgenticChatInterface className="h-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">CEP Machine Dashboard</h1>
              <p className="text-gray-600">9-Layer AI Agent Framework for Business Automation</p>
            </div>
            <button
              onClick={() => setActiveView("chat")}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Open AI Assistant
            </button>
          </div>
          
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Active Layers", value: "9", change: "+0" },
              { label: "Prospects Found", value: "247", change: "+12" },
              { label: "Campaigns Active", value: "3", change: "+1" },
              { label: "Revenue Tracked", value: "$12.4k", change: "+$2.1k" },
            ].map((stat, index) => (
              <div key={index} className="bg-white rounded-lg border p-4">
                <p className="text-sm text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-xs text-green-600">{stat.change}</p>
              </div>
            ))}
          </div>
          
          {/* Layer Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {layers.map((layer) => (
              <div
                key={layer.id}
                className="p-4 rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all cursor-pointer bg-white"
                onClick={() => setActiveView("chat")}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                    {layer.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Layer {layer.id}</h3>
                    <p className="text-sm text-gray-600">{layer.name}</p>
                  </div>
                </div>
                <p className="text-xs text-gray-500">{layer.desc}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">Active</span>
                  <span className="text-xs text-gray-400">Click to interact →</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
