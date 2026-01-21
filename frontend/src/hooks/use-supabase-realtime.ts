"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@supabase/supabase-js";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export function useSupabaseRealtime() {
  const [supabase] = useState(() => createClient(supabaseUrl, supabaseAnonKey));
  const [subscriptions, setSubscriptions] = useState<Map<string, any>>(new Map());
  const [realtimeData, setRealtimeData] = useState<Record<string, any>>({});

  // Subscribe to table changes
  const subscribe = useCallback((table: string, filter?: string) => {
    const subscriptionKey = `${table}_${filter || "all"}`;
    
    // Check if already subscribed
    if (subscriptions.has(subscriptionKey)) {
      return subscriptions.get(subscriptionKey);
    }

    const channel = supabase
      .channel(`realtime_${subscriptionKey}`)
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table,
          filter
        },
        (payload) => {
          console.log(`Realtime update for ${table}:`, payload);
          
          // Update local state
          setRealtimeData(prev => ({
            ...prev,
            [subscriptionKey]: {
              event: payload.eventType,
              data: payload.new || payload.old,
              timestamp: new Date().toISOString()
            }
          }));
        }
      )
      .subscribe();

    // Store subscription
    setSubscriptions(prev => new Map(prev.set(subscriptionKey, channel)));

    return channel;
  }, [supabase, subscriptions]);

  // Unsubscribe from table
  const unsubscribe = useCallback((table: string, filter?: string) => {
    const subscriptionKey = `${table}_${filter || "all"}`;
    const channel = subscriptions.get(subscriptionKey);
    
    if (channel) {
      supabase.removeChannel(channel);
      setSubscriptions(prev => {
        const newMap = new Map(prev);
        newMap.delete(subscriptionKey);
        return newMap;
      });
    }
  }, [supabase, subscriptions]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      subscriptions.forEach(channel => {
        supabase.removeChannel(channel);
      });
    };
  }, [supabase, subscriptions]);

  return {
    subscribe,
    unsubscribe,
    realtimeData,
    subscriptions: Array.from(subscriptions.keys())
  };
}

// Hook for prospect real-time updates
export function useProspectRealtime() {
  const { subscribe, unsubscribe, realtimeData } = useSupabaseRealtime();
  const [prospects, setProspects] = useState<any[]>([]);

  // Expose prospects to CopilotKit
  useCopilotReadable({
    description: "Current prospects with real-time updates",
    value: prospects
  });

  // Action to add prospect
  useCopilotAction({
    name: "add_prospect",
    description: "Add a new prospect",
    parameters: ["business_name", "location", "category", "phone", "website"],
    handler: async ({ business_name, location, category, phone, website }) => {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data, error } = await supabase
        .from("prospects")
        .insert({
          business_name,
          location,
          category,
          phone,
          website,
          status: "new",
          created_at: new Date().toISOString()
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    }
  });

  // Subscribe to prospects table
  useEffect(() => {
    const channel = subscribe("prospects");
    
    // Load initial prospects
    const loadProspects = async () => {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data } = await supabase
        .from("prospects")
        .select("*")
        .order("created_at", { ascending: false });
      
      if (data) setProspects(data);
    };

    loadProspects();

    return () => {
      unsubscribe("prospects");
    };
  }, [subscribe, unsubscribe]);

  // Update prospects when realtime data changes
  useEffect(() => {
    const prospectUpdates = realtimeData["prospects_all"];
    if (prospectUpdates) {
      if (prospectUpdates.event === "INSERT") {
        setProspects(prev => [prospectUpdates.data, ...prev]);
      } else if (prospectUpdates.event === "UPDATE") {
        setProspects(prev => 
          prev.map(p => p.id === prospectUpdates.data.id ? prospectUpdates.data : p)
        );
      } else if (prospectUpdates.event === "DELETE") {
        setProspects(prev => prev.filter(p => p.id !== prospectUpdates.data.id));
      }
    }
  }, [realtimeData]);

  return { prospects };
}

// Hook for agent status real-time updates
export function useAgentStatusRealtime() {
  const { subscribe, unsubscribe, realtimeData } = useSupabaseRealtime();
  const [agentStatus, setAgentStatus] = useState<Record<string, any>>({});

  // Expose agent status to CopilotKit
  useCopilotReadable({
    description: "Real-time agent status and metrics",
    value: agentStatus
  });

  // Subscribe to agent_status table
  useEffect(() => {
    const channel = subscribe("agent_status");
    
    // Load initial agent status
    const loadAgentStatus = async () => {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data } = await supabase
        .from("agent_status")
        .select("*")
        .order("updated_at", { ascending: false });
      
      if (data) {
        const statusMap: Record<string, any> = {};
        data.forEach(status => {
          statusMap[status.agent_id] = status;
        });
        setAgentStatus(statusMap);
      }
    };

    loadAgentStatus();

    return () => {
      unsubscribe("agent_status");
    };
  }, [subscribe, unsubscribe]);

  // Update agent status when realtime data changes
  useEffect(() => {
    const statusUpdates = realtimeData["agent_status_all"];
    if (statusUpdates) {
      setAgentStatus(prev => ({
        ...prev,
        [statusUpdates.data.agent_id]: statusUpdates.data
      }));
    }
  }, [realtimeData]);

  // Action to update agent status
  useCopilotAction({
    name: "update_agent_status",
    description: "Update agent status",
    parameters: ["agent_id", "status", "progress", "message"],
    handler: async ({ agent_id, status, progress, message }) => {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data, error } = await supabase
        .from("agent_status")
        .upsert({
          agent_id,
          status,
          progress: progress || 0,
          message,
          updated_at: new Date().toISOString()
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    }
  });

  return { agentStatus };
}

// Hook for metrics real-time updates
export function useMetricsRealtime() {
  const { subscribe, unsubscribe, realtimeData } = useSupabaseRealtime();
  const [metrics, setMetrics] = useState<any>({});

  // Expose metrics to CopilotKit
  useCopilotReadable({
    description: "Real-time system metrics",
    value: metrics
  });

  // Subscribe to metrics table
  useEffect(() => {
    const channel = subscribe("metrics", "id=eq.1");
    
    // Load initial metrics
    const loadMetrics = async () => {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data } = await supabase
        .from("metrics")
        .select("*")
        .eq("id", 1)
        .single();
      
      if (data) setMetrics(data);
    };

    loadMetrics();

    return () => {
      unsubscribe("metrics", "id=eq.1");
    };
  }, [subscribe, unsubscribe]);

  // Update metrics when realtime data changes
  useEffect(() => {
    const metricsUpdates = realtimeData["metrics_id=eq.1"];
    if (metricsUpdates) {
      setMetrics(metricsUpdates.data);
    }
  }, [realtimeData]);

  return { metrics };
}

// Hook for coherence metrics real-time updates
export function useCoherenceRealtime() {
  const { subscribe, unsubscribe, realtimeData } = useSupabaseRealtime();
  const [coherence, setCoherence] = useState<any>({});

  // Expose coherence to CopilotKit
  useCopilotReadable({
    description: "Real-time coherence metrics",
    value: coherence
  });

  // Subscribe to coherence_metrics table
  useEffect(() => {
    const channel = subscribe("coherence_metrics");
    
    // Load initial coherence
    const loadCoherence = async () => {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data } = await supabase
        .from("coherence_metrics")
        .select("*")
        .order("timestamp", { ascending: false })
        .limit(1)
        .single();
      
      if (data) setCoherence(data);
    };

    loadCoherence();

    return () => {
      unsubscribe("coherence_metrics");
    };
  }, [subscribe, unsubscribe]);

  // Update coherence when realtime data changes
  useEffect(() => {
    const coherenceUpdates = realtimeData["coherence_metrics_all"];
    if (coherenceUpdates) {
      setCoherence(coherenceUpdates.data);
    }
  }, [realtimeData]);

  // Action to update coherence
  useCopilotAction({
    name: "update_coherence",
    description: "Update coherence metrics",
    parameters: ["phi_sync", "layer_coherence", "system_health"],
    handler: async ({ phi_sync, layer_coherence, system_health }) => {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data, error } = await supabase
        .from("coherence_metrics")
        .insert({
          phi_sync,
          layer_coherence,
          system_health,
          timestamp: new Date().toISOString()
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    }
  });

  return { coherence };
}
