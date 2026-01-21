"use client";

import { CopilotSidebar, CopilotChat } from "@copilotkit/react-ui";
import { useState } from "react";

export default function HomePage() {
  const [activeLayer, setActiveLayer] = useState<string | null>(null);

  return (
    <div className="flex h-screen bg-gray-50">
      <CopilotSidebar
        defaultOpen={false}
        labels={{
          title: "CEP Machine Assistant",
          initial: "I help you manage business automation workflows. Which layer would you like to work with?",
        }}
      />
      
      <main className="flex-1 p-6 overflow-auto">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">CEP Machine Dashboard</h1>
          <p className="text-gray-600 mb-8">9-Layer AI Agent Framework for Business Automation</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {[
              { id: "1", name: "Prospect Research", desc: "Find businesses with weak GBP" },
              { id: "2", name: "Pitch Generator", desc: "Personalized outreach content" },
              { id: "3", name: "Outreach Engine", desc: "Multi-channel message delivery" },
              { id: "4", name: "Booking Handler", desc: "Calendly webhook to CRM" },
              { id: "5", name: "Onboarding Flow", desc: "Automated client setup" },
              { id: "6", name: "GBP Optimizer", desc: "Google Business Profile automation" },
              { id: "7", name: "Reporting Engine", desc: "Performance analytics with AI" },
              { id: "8", name: "Finance Tracker", desc: "Revenue and expense tracking" },
              { id: "9", name: "Self-Learning", desc: "Feedback loop for improvement" },
            ].map((layer) => (
              <div
                key={layer.id}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  activeLayer === layer.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                onClick={() => setActiveLayer(layer.id)}
              >
                <h3 className="font-semibold text-gray-900">Layer {layer.id}</h3>
                <p className="text-sm text-gray-600 mt-1">{layer.name}</p>
                <p className="text-xs text-gray-500 mt-2">{layer.desc}</p>
              </div>
            ))}
          </div>
          
          {activeLayer && (
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">
                Layer {activeLayer} - Active
              </h2>
              <CopilotChat
                labels={{
                  title: `Layer ${activeLayer} Chat`,
                  initial: `Working with Layer ${activeLayer}. How can I assist?`,
                }}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
