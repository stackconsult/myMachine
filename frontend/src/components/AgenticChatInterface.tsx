"use client";

import { useState, useCallback } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { Bot, User, Wrench, Sparkles, Brain } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface AgentCapability {
  name: string;
  description: string;
  icon: React.ReactNode;
  tools: string[];
}

interface AdvancedChatProps {
  className?: string;
  agent?: string;
  capabilities?: AgentCapability[];
}

const AGENT_CAPABILITIES: AgentCapability[] = [
  {
    name: "Business Growth",
    description: "Prospect research, pitch generation, outreach campaigns",
    icon: <Brain className="w-4 h-4" />,
    tools: ["search_prospects", "generate_pitch", "send_outreach"]
  },
  {
    name: "Performance Analysis",
    description: "Analytics, reporting, optimization insights",
    icon: <Sparkles className="w-4 h-4" />,
    tools: ["analyze_performance", "generate_report"]
  },
  {
    name: "Finance Tracking",
    description: "Transaction monitoring, financial analytics",
    icon: <Wrench className="w-4 h-4" />,
    tools: ["track_finances"]
  }
];

export function AgenticChatInterface({ 
  className, 
  agent = "cep_machine",
  capabilities = AGENT_CAPABILITIES 
}: AdvancedChatProps) {
  const [selectedCapability, setSelectedCapability] = useState<string | null>(null);
  const [isExecutingTool, setIsExecutingTool] = useState(false);
  
  const {
    isLoading,
  } = useCopilotChat();

  const handleCapabilitySelect = useCallback((capabilityName: string) => {
    setSelectedCapability(capabilityName);
    const capability = capabilities.find(c => c.name === capabilityName);
    if (capability) {
      const prompt = `I want to use ${capability.name} capabilities. ${capability.description}. What can you help me with?`;
      // Use the chat interface to send message
      const inputElement = document.querySelector('textarea[placeholder*="Describe"]') as HTMLTextAreaElement;
      if (inputElement) {
        inputElement.value = prompt;
        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  }, [capabilities]);

  const customInstructions = `
    You are an advanced AI assistant with access to specialized business automation agents.
    You have the following capabilities:
    
    ${capabilities.map(cap => `
    ${cap.name}: ${cap.description}
    Available tools: ${cap.tools.join(", ")}
    `).join("\n")}
    
    Guidelines:
    1. Always identify which agent capability is needed based on user intent
    2. Execute tools automatically when appropriate
    3. Provide detailed explanations of tool results
    4. Suggest follow-up actions based on results
    5. Maintain context across conversations
    6. Be proactive in suggesting relevant capabilities
  `;

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Agent Capabilities Selector */}
      <div className="p-4 border-b bg-white">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Available Capabilities</h3>
        <div className="flex gap-2 flex-wrap">
          {capabilities.map((capability) => (
            <motion.button
              key={capability.name}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleCapabilitySelect(capability.name)}
              className={cn(
                "px-3 py-2 rounded-lg border text-xs font-medium transition-colors",
                selectedCapability === capability.name
                  ? "bg-blue-500 text-white border-blue-500"
                  : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
              )}
            >
              <span className="flex items-center gap-2">
                {capability.icon}
                {capability.name}
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Chat Interface */}
      <div className="flex-1 flex flex-col">
        <CopilotChat
          instructions={customInstructions}
          labels={{
            title: "Advanced AI Assistant",
            initial: "Select a capability or ask me anything about business automation...",
            placeholder: "Describe what you'd like to accomplish...",
          }}
          className="flex-1"
        />
      </div>

      {/* Status Indicator */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="p-2 bg-blue-50 border-t border-blue-200"
          >
            <div className="flex items-center gap-2 text-sm text-blue-700">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              {isExecutingTool ? "Executing tool..." : "AI Assistant is thinking..."}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
