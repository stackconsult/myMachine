"use client";

import { useState, useCallback } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { Message, CopilotKitProps } from "@copilotkit/react-ui";
import { Bot, User, Tool, Sparkles, Brain } from "lucide-react";
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
    icon: <Tool className="w-4 h-4" />,
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
    messages,
    setMessages,
    appendMessage,
    deleteMessage,
    reloadMessages,
    stopGeneration,
    isLoading,
  } = useCopilotChat();

  const handleCapabilitySelect = useCallback((capabilityName: string) => {
    setSelectedCapability(capabilityName);
    const capability = capabilities.find(c => c.name === capabilityName);
    if (capability) {
      const prompt = `I want to use ${capability.name} capabilities. ${capability.description}. What can you help me with?`;
      appendMessage({
        role: "user",
        content: prompt,
      });
    }
  }, [capabilities, appendMessage]);

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

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === "user";
    const isToolExecution = message.content?.includes("tool") || message.content?.includes("executing");
    
    return (
      <motion.div
        key={index}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={cn(
          "flex gap-3 p-4 rounded-lg",
          isUser ? "bg-blue-50 ml-auto max-w-[80%]" : "bg-gray-50 mr-auto max-w-[80%]"
        )}
      >
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isUser ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-600"
        )}>
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium mb-1">
            {isUser ? "You" : "AI Assistant"}
          </div>
          <div className="text-sm whitespace-pre-wrap">
            {message.content}
          </div>
          {isToolExecution && (
            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
              <Tool className="w-3 h-3 inline mr-1" />
              Executing tool...
            </div>
          )}
        </div>
      </motion.div>
    );
  };

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
          renderMessage={renderMessage}
          onMessageSubmit={(message) => {
            console.log("Message submitted:", message);
          }}
          onGenerationStop={() => {
            setIsExecutingTool(false);
          }}
          onMessageReload={() => {
            console.log("Messages reloaded");
          }}
          onMessageCopy={(message) => {
            console.log("Message copied:", message);
          }}
          onThumbsUp={(message) => {
            console.log("Thumbs up:", message);
          }}
          onThumbsDown={(message) => {
            console.log("Thumbs down:", message);
          }}
          suggestions={[
            "Find prospects in New York for restaurants",
            "Generate a pitch for a dental clinic",
            "Analyze performance for last month",
            "Track a new financial transaction",
            "Optimize Google Business Profile",
          ]}
          autoSuggestions={true}
          enableImageUpload={false}
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
