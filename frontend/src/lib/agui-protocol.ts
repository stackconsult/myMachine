/**
 * AG-UI Protocol Implementation
 * Google's Agent-to-UI protocol for bidirectional communication
 */

import { useState, useEffect } from "react";

export interface AGUIMessage {
  type: "ui" | "state" | "action" | "response";
  id: string;
  timestamp: string;
  agentId?: string;
  data?: any;
}

export interface AGUIComponent {
  id: string;
  type: string;
  props?: Record<string, any>;
  children?: AGUIComponent[];
  state?: any;
}

export interface AGUIState {
  components: AGUIComponent[];
  globalState: Record<string, any>;
  agentState: Record<string, any>;
}

export class AGUIProtocol {
  private ws: WebSocket | null = null;
  private messageQueue: AGUIMessage[] = [];
  private state: AGUIState;
  private listeners: Map<string, (message: AGUIMessage) => void> = new Map();
  private isConnected = false;

  constructor(private agentId: string) {
    this.state = {
      components: [],
      globalState: {},
      agentState: {}
    };
  }

  /**
   * Connect to AG-UI endpoint
   */
  async connect(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${url}/ws/agent/${this.agentId}`);
        
        this.ws.onopen = () => {
          this.isConnected = true;
          console.log(`AG-UI Connected for agent ${this.agentId}`);
          
          // Send queued messages
          while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
          }
          
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          const message: AGUIMessage = JSON.parse(event.data);
          this.handleMessage(message);
        };
        
        this.ws.onerror = (error) => {
          console.error("AG-UI WebSocket error:", error);
          reject(error);
        };
        
        this.ws.onclose = () => {
          this.isConnected = false;
          console.log("AG-UI Disconnected");
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from AG-UI endpoint
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  /**
   * Send message to agent
   */
  send(message: Partial<AGUIMessage>): void {
    const fullMessage: AGUIMessage = {
      type: message.type || "action",
      id: message.id || this.generateId(),
      timestamp: new Date().toISOString(),
      agentId: this.agentId,
      data: message.data
    };

    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify(fullMessage));
    } else {
      // Queue message for when connected
      this.messageQueue.push(fullMessage);
    }
  }

  /**
   * Send UI component to agent
   */
  sendComponent(component: AGUIComponent): void {
    this.send({
      type: "ui",
      data: { component }
    });
  }

  /**
   * Send state update to agent
   */
  sendState(state: Partial<AGUIState>): void {
    this.state = { ...this.state, ...state };
    this.send({
      type: "state",
      data: { state: this.state }
    });
  }

  /**
   * Send action to agent
   */
  sendAction(action: string, data?: any): void {
    this.send({
      type: "action",
      data: { action, data }
    });
  }

  /**
   * Listen for specific message types
   */
  on(type: string, listener: (message: AGUIMessage) => void): void {
    this.listeners.set(type, listener);
  }

  /**
   * Remove listener
   */
  off(type: string): void {
    this.listeners.delete(type);
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(message: AGUIMessage): void {
    // Update state based on message type
    switch (message.type) {
      case "ui":
        if (message.data?.component) {
          this.updateComponent(message.data.component);
        }
        break;
      case "state":
        if (message.data?.state) {
          this.state = message.data.state;
        }
        break;
    }

    // Notify listeners
    const listener = this.listeners.get(message.type);
    if (listener) {
      listener(message);
    }

    // Notify all listeners
    this.listeners.forEach(listener => listener(message));
  }

  /**
   * Update component in state
   */
  private updateComponent(component: AGUIComponent): void {
    const updateComponentTree = (components: AGUIComponent[]): AGUIComponent[] => {
      return components.map(comp => {
        if (comp.id === component.id) {
          return { ...comp, ...component };
        }
        if (comp.children) {
          return { ...comp, children: updateComponentTree(comp.children) };
        }
        return comp;
      });
    };

    this.state.components = updateComponentTree(this.state.components);
  }

  /**
   * Get component by ID
   */
  getComponent(id: string): AGUIComponent | null {
    const findComponent = (components: AGUIComponent[]): AGUIComponent | null => {
      for (const comp of components) {
        if (comp.id === id) return comp;
        if (comp.children) {
          const found = findComponent(comp.children);
          if (found) return found;
        }
      }
      return null;
    };

    return findComponent(this.state.components);
  }

  /**
   * Get all components of type
   */
  getComponentsByType(type: string): AGUIComponent[] {
    const findByType = (components: AGUIComponent[]): AGUIComponent[] => {
      let found: AGUIComponent[] = [];
      
      for (const comp of components) {
        if (comp.type === type) found.push(comp);
        if (comp.children) {
          found = [...found, ...findByType(comp.children)];
        }
      }
      
      return found;
    };

    return findByType(this.state.components);
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `agui_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current state
   */
  getState(): AGUIState {
    return this.state;
  }

  /**
   * Check if connected
   */
  isAGUIConnected(): boolean {
    return this.isConnected;
  }
}

/**
 * AG-UI Component Factory
 */
export class AGUIComponentFactory {
  static createButton(id: string, props: any = {}): AGUIComponent {
    return {
      id,
      type: "button",
      props: {
        label: "Button",
        variant: "primary",
        ...props
      }
    };
  }

  static createInput(id: string, props: any = {}): AGUIComponent {
    return {
      id,
      type: "input",
      props: {
        type: "text",
        placeholder: "Enter value...",
        ...props
      }
    };
  }

  static createText(id: string, text: string, props: any = {}): AGUIComponent {
    return {
      id,
      type: "text",
      props: {
        content: text,
        ...props
      }
    };
  }

  static createCard(id: string, title: string, children: AGUIComponent[] = [], props: any = {}): AGUIComponent {
    return {
      id,
      type: "card",
      props: {
        title,
        ...props
      },
      children
    };
  }

  static createForm(id: string, fields: any[], props: any = {}): AGUIComponent {
    const children = fields.map(field => {
      switch (field.type) {
        case "input":
          return this.createInput(field.id, field.props);
        case "text":
          return this.createText(field.id, field.content, field.props);
        default:
          return this.createText(field.id, "Unknown field type");
      }
    });

    return {
      id,
      type: "form",
      props: {
        ...props
      },
      children
    };
  }

  static createChart(id: string, data: any[], props: any = {}): AGUIComponent {
    return {
      id,
      type: "chart",
      props: {
        data,
        chartType: "line",
        ...props
      }
    };
  }

  static createTable(id: string, columns: any[], rows: any[][], props: any = {}): AGUIComponent {
    return {
      id,
      type: "table",
      props: {
        columns,
        rows,
        ...props
      }
    };
  }

  static createContainer(id: string, children: AGUIComponent[], props: any = {}): AGUIComponent {
    return {
      id,
      type: "container",
      props: {
        direction: "column",
        spacing: "medium",
        ...props
      },
      children
    };
  }
}

/**
 * AG-UI State Manager
 */
export class AGUIStateManager {
  private state: Map<string, any> = new Map();
  private subscribers: Map<string, Set<(value: any) => void>> = new Map();

  /**
   * Set state value
   */
  set(key: string, value: any): void {
    this.state.set(key, value);
    this.notifySubscribers(key, value);
  }

  /**
   * Get state value
   */
  get(key: string): any {
    return this.state.get(key);
  }

  /**
   * Subscribe to state changes
   */
  subscribe(key: string, callback: (value: any) => void): () => void {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }
    
    this.subscribers.get(key)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const subs = this.subscribers.get(key);
      if (subs) {
        subs.delete(callback);
        if (subs.size === 0) {
          this.subscribers.delete(key);
        }
      }
    };
  }

  /**
   * Notify subscribers of state change
   */
  private notifySubscribers(key: string, value: any): void {
    const subs = this.subscribers.get(key);
    if (subs) {
      subs.forEach(callback => callback(value));
    }
  }

  /**
   * Get all state
   */
  getAll(): Record<string, any> {
    return Object.fromEntries(this.state);
  }

  /**
   * Clear all state
   */
  clear(): void {
    this.state.clear();
    this.subscribers.clear();
  }
}

/**
 * AG-UI React Hook
 */
export function useAGUI(agentId: string) {
  const [protocol] = useState(() => new AGUIProtocol(agentId));
  const [state, setState] = useState<AGUIState>(protocol.getState());

  useEffect(() => {
    // Connect to AG-UI endpoint
    const connect = async () => {
      try {
        await protocol.connect("ws://localhost:8000");
      } catch (error) {
        console.error("Failed to connect to AG-UI:", error);
      }
    };

    connect();

    // Listen for state updates
    const handleStateUpdate = (message: AGUIMessage) => {
      if (message.type === "state") {
        setState(message.data?.state || protocol.getState());
      }
    };

    protocol.on("state", handleStateUpdate);

    return () => {
      protocol.off("state");
      protocol.disconnect();
    };
  }, [agentId]);

  return {
    protocol,
    state,
    sendComponent: protocol.sendComponent.bind(protocol),
    sendState: protocol.sendState.bind(protocol),
    sendAction: protocol.sendAction.bind(protocol),
    isConnected: protocol.isAGUIConnected()
  };
}
