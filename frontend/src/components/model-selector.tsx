"use client";

import { useState } from "react";

interface ModelConfig {
  provider: string;
  model: string;
  apiKey: string;
  endpoint?: string;
}

const MODEL_OPTIONS = {
  openai: {
    name: "OpenAI",
    models: [
      { id: "gpt-4-turbo", name: "GPT-4 Turbo" },
      { id: "gpt-4", name: "GPT-4" },
      { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo" }
    ]
  },
  anthropic: {
    name: "Anthropic",
    models: [
      { id: "claude-3-opus", name: "Claude 3 Opus" },
      { id: "claude-3-sonnet", name: "Claude 3 Sonnet" },
      { id: "claude-3-haiku", name: "Claude 3 Haiku" }
    ]
  },
  groq: {
    name: "Groq",
    models: [
      { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B" },
      { id: "llama2-70b-4096", name: "Llama2 70B" },
      { id: "gemma-7b-it", name: "Gemma 7B" }
    ]
  },
  local: {
    name: "Local Models",
    models: [
      { id: "ollama-llama2", name: "Ollama Llama2" },
      { id: "ollama-mistral", name: "Ollama Mistral" },
      { id: "custom", name: "Custom Endpoint" }
    ]
  }
};

export default function ModelSelector() {
  const [selectedProvider, setSelectedProvider] = useState("openai");
  const [selectedModel, setSelectedModel] = useState("gpt-4-turbo");
  const [configs, setConfigs] = useState<Record<string, ModelConfig>>({
    openai: { provider: "openai", model: "gpt-4-turbo", apiKey: "" },
    anthropic: { provider: "anthropic", model: "claude-3-sonnet", apiKey: "" },
    groq: { provider: "groq", model: "mixtral-8x7b-32768", apiKey: "" },
    local: { provider: "local", model: "ollama-llama2", apiKey: "", endpoint: "http://localhost:11434" }
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    const config = configs[provider];
    setSelectedModel(config.model);
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setConfigs(prev => ({
      ...prev,
      [selectedProvider]: { ...prev[selectedProvider], model }
    }));
  };

  const handleApiKeyChange = (apiKey: string) => {
    setConfigs(prev => ({
      ...prev,
      [selectedProvider]: { ...prev[selectedProvider], apiKey }
    }));
  };

  const handleEndpointChange = (endpoint: string) => {
    setConfigs(prev => ({
      ...prev,
      [selectedProvider]: { ...prev[selectedProvider], endpoint }
    }));
  };

  const saveConfiguration = async () => {
    const config = configs[selectedProvider];
    
    // Save to backend
    try {
      const response = await fetch("/api/config/model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        alert("Model configuration saved successfully!");
      } else {
        alert("Failed to save configuration");
      }
    } catch (error) {
      console.error("Save error:", error);
      alert("Failed to save configuration");
    }
  };

  const testConnection = async () => {
    const config = configs[selectedProvider];
    
    try {
      const response = await fetch("/api/test/model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert("Connection successful!");
      } else {
        alert(`Connection failed: ${result.error}`);
      }
    } catch (error) {
      console.error("Test error:", error);
      alert("Failed to test connection");
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Model Configuration</h2>
      
      {/* Provider Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Model Provider
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {Object.entries(MODEL_OPTIONS).map(([key, provider]) => (
            <button
              key={key}
              onClick={() => handleProviderChange(key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedProvider === key
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {provider.name}
            </button>
          ))}
        </div>
      </div>

      {/* Model Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Model
        </label>
        <select
          value={selectedModel}
          onChange={(e) => handleModelChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {MODEL_OPTIONS[selectedProvider].models.map(model => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
      </div>

      {/* API Key */}
      {selectedProvider !== "local" && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API Key
          </label>
          <input
            type="password"
            value={configs[selectedProvider].apiKey}
            onChange={(e) => handleApiKeyChange(e.target.value)}
            placeholder={`Enter ${MODEL_OPTIONS[selectedProvider].name} API key`}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Custom Endpoint (for local models) */}
      {selectedProvider === "local" && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Endpoint URL
          </label>
          <input
            type="url"
            value={configs[selectedProvider].endpoint || ""}
            onChange={(e) => handleEndpointChange(e.target.value)}
            placeholder="http://localhost:11434"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Advanced Settings */}
      <div className="mb-6">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {showAdvanced ? "Hide" : "Show"} Advanced Settings
        </button>
        
        {showAdvanced && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  defaultValue="0.7"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  min="1"
                  max="4096"
                  defaultValue="2048"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2">
        <button
          onClick={testConnection}
          className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          Test Connection
        </button>
        <button
          onClick={saveConfiguration}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Save Configuration
        </button>
      </div>

      {/* Model Info */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">Model Information</h3>
        <div className="text-sm text-blue-800">
          <p><strong>Provider:</strong> {MODEL_OPTIONS[selectedProvider].name}</p>
          <p><strong>Model:</strong> {MODEL_OPTIONS[selectedProvider].models.find(m => m.id === selectedModel)?.name}</p>
          {selectedProvider === "local" && (
            <p className="mt-2">
              <strong>Note:</strong> Make sure your local model server is running at the specified endpoint.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
