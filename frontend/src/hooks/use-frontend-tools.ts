"use client";

import { useFrontendTool } from "@copilotkit/react-core";
import { useState } from "react";

// Frontend tools for CEP Machine
export function useProspectTools() {
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  // Tool to search prospects
  const searchProspectsTool = useFrontendTool({
    name: "search_prospects",
    description: "Search for business prospects",
    parameters: ["location", "category", "limit"],
    handler: async ({ location, category, limit = 10 }) => {
      setIsSearching(true);
      try {
        // Call backend API
        const response = await fetch("/api/prospects/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ location, category, limit }),
        });
        const data = await response.json();
        setResults(data.prospects || []);
        return data;
      } catch (error) {
        console.error("Search error:", error);
        return { error: "Failed to search prospects" };
      } finally {
        setIsSearching(false);
      }
    },
  });

  // Tool to save prospect
  const saveProspectTool = useFrontendTool({
    name: "save_prospect",
    description: "Save a prospect to database",
    parameters: ["prospect_data"],
    handler: async ({ prospect_data }) => {
      try {
        const response = await fetch("/api/prospects/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(prospect_data),
        });
        return await response.json();
      } catch (error) {
        console.error("Save error:", error);
        return { error: "Failed to save prospect" };
      }
    },
  });

  return {
    searchProspects: searchProspectsTool,
    saveProspect: saveProspectTool,
    isSearching,
    results,
  };
}

export function usePitchTools() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [pitch, setPitch] = useState<any>(null);

  // Tool to generate pitch
  const generatePitchTool = useFrontendTool({
    name: "generate_pitch",
    description: "Generate personalized pitch",
    parameters: ["prospect_id", "channel"],
    handler: async ({ prospect_id, channel }) => {
      setIsGenerating(true);
      try {
        const response = await fetch("/api/pitches/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prospect_id, channel }),
        });
        const data = await response.json();
        setPitch(data);
        return data;
      } catch (error) {
        console.error("Generation error:", error);
        return { error: "Failed to generate pitch" };
      } finally {
        setIsGenerating(false);
      }
    },
  });

  // Tool to send pitch
  const sendPitchTool = useFrontendTool({
    name: "send_pitch",
    description: "Send pitch via email/SMS/LinkedIn",
    parameters: ["pitch_id", "channel"],
    handler: async ({ pitch_id, channel }) => {
      try {
        const response = await fetch("/api/pitches/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pitch_id, channel }),
        });
        return await response.json();
      } catch (error) {
        console.error("Send error:", error);
        return { error: "Failed to send pitch" };
      }
    },
  });

  return {
    generatePitch: generatePitchTool,
    sendPitch: sendPitchTool,
    isGenerating,
    pitch,
  };
}

export function useOutreachTools() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [sequences, setSequences] = useState<any[]>([]);

  // Tool to plan outreach sequence
  const planSequenceTool = useFrontendTool({
    name: "plan_outreach_sequence",
    description: "Plan multi-channel outreach sequence",
    parameters: ["prospect_id", "channels"],
    handler: async ({ prospect_id, channels }) => {
      setIsExecuting(true);
      try {
        const response = await fetch("/api/outreach/plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prospect_id, channels }),
        });
        const data = await response.json();
        setSequences(prev => [...prev, data]);
        return data;
      } catch (error) {
        console.error("Planning error:", error);
        return { error: "Failed to plan sequence" };
      } finally {
        setIsExecuting(false);
      }
    },
  });

  // Tool to execute outreach
  const executeOutreachTool = useFrontendTool({
    name: "execute_outreach",
    description: "Execute outreach sequence",
    parameters: ["sequence_id"],
    handler: async ({ sequence_id }) => {
      try {
        const response = await fetch("/api/outreach/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sequence_id }),
        });
        return await response.json();
      } catch (error) {
        console.error("Execution error:", error);
        return { error: "Failed to execute outreach" };
      }
    },
  });

  return {
    planSequence: planSequenceTool,
    executeOutreach: executeOutreachTool,
    isExecuting,
    sequences,
  };
}

export function useReportingTools() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [report, setReport] = useState<any>(null);

  // Tool to generate report
  const generateReportTool = useFrontendTool({
    name: "generate_report",
    description: "Generate performance report",
    parameters: ["report_type", "date_range"],
    handler: async ({ report_type, date_range }) => {
      setIsGenerating(true);
      try {
        const response = await fetch("/api/reports/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ report_type, date_range }),
        });
        const data = await response.json();
        setReport(data);
        return data;
      } catch (error) {
        console.error("Report generation error:", error);
        return { error: "Failed to generate report" };
      } finally {
        setIsGenerating(false);
      }
    },
  });

  // Tool to export report
  const exportReportTool = useFrontendTool({
    name: "export_report",
    description: "Export report to PDF/Excel",
    parameters: ["report_id", "format"],
    handler: async ({ report_id, format }) => {
      try {
        const response = await fetch(`/api/reports/${report_id}/export?format=${format}`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `report.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
        return { success: true };
      } catch (error) {
        console.error("Export error:", error);
        return { error: "Failed to export report" };
      }
    },
  });

  return {
    generateReport: generateReportTool,
    exportReport: exportReportTool,
    isGenerating,
    report,
  };
}
