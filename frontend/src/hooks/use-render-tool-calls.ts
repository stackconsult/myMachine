"use client";

import { useRenderToolCall } from "@copilotkit/react-core";
import { useState } from "react";
import A2UIRenderer from "@/components/ui/a2ui-renderer";

// Render Tool Call hooks for dynamic UI generation
export function useToolRenderer() {
  const [renderedComponents, setRenderedComponents] = useState<any[]>([]);
  const [isRendering, setIsRendering] = useState(false);

  // Configure tool call renderer
  const renderTool = useRenderToolCall({
    name: "render_ui",
    description: "Render dynamic UI components",
    handler: async (toolCall: any) => {
      setIsRendering(true);
      try {
        const { component } = toolCall;
        
        // Add to rendered components
        setRenderedComponents((prev: any[]) => [...prev, {
          id: toolCall.id,
          component,
          timestamp: new Date().toISOString()
        }]);
        
        return { rendered: true };
      } catch (error) {
        console.error("Render error:", error);
        return { error: "Failed to render component" };
      } finally {
        setIsRendering(false);
      }
    },
  });

  // Render A2UI components
  const renderA2UI = useRenderToolCall({
    name: "render_a2ui",
    description: "Render A2UI specification",
    handler: async (toolCall: any) => {
      setIsRendering(true);
      try {
        const { a2ui_spec } = toolCall;
        
        // Render A2UI component
        const component = (
          <A2UIRenderer
            component={a2ui_spec}
            onAction={(action: string, data: any) => {
              // Handle component actions
              console.log("A2UI Action:", action, data);
            }}
          />
        );
        
        setRenderedComponents((prev: any[]) => [...prev, {
          id: toolCall.id,
          component,
          type: "a2ui",
          timestamp: new Date().toISOString()
        }]);
        
        return { rendered: true };
      } catch (error) {
        console.error("A2UI render error:", error);
        return { error: "Failed to render A2UI" };
      } finally {
        setIsRendering(false);
      }
    },
  });

  // Clear rendered components
  const clearRendered = () => {
    setRenderedComponents([]);
  };

  return {
    renderTool,
    renderA2UI,
    renderedComponents,
    isRendering,
    clearRendered,
  };
}

export function useDashboardRenderer() {
  const [dashboardWidgets, setDashboardWidgets] = useState<any[]>([]);
  const [layout, setLayout] = useState<any>(null);

  // Render dashboard widgets
  const renderDashboard = useRenderToolCall({
    name: "render_dashboard",
    description: "Render dashboard widgets",
    handler: async (toolCall: any) => {
      try {
        const { widgets, layout: widgetLayout } = toolCall;
        
        // Update dashboard state
        setDashboardWidgets(widgets || []);
        setLayout(widgetLayout || null);
        
        return { rendered: true };
      } catch (error) {
        console.error("Dashboard render error:", error);
        return { error: "Failed to render dashboard" };
      }
    },
  });

  // Update widget data
  const updateWidget = useRenderToolCall({
    name: "update_widget",
    description: "Update widget data",
    handler: async (toolCall: any) => {
      try {
        const { widget_id, data } = toolCall;
        
        setDashboardWidgets(prev => 
          prev.map(widget => 
            widget.id === widget_id 
              ? { ...widget, data: { ...widget.data, ...data } }
              : widget
          )
        );
        
        return { updated: true };
      } catch (error) {
        console.error("Widget update error:", error);
        return { error: "Failed to update widget" };
      }
    },
  });

  return {
    renderDashboard,
    updateWidget,
    dashboardWidgets,
    layout,
  };
}

export function useFormRenderer() {
  const [forms, setForms] = useState<any[]>([]);
  const [activeForm, setActiveForm] = useState<any>(null);

  // Render dynamic forms
  const renderForm = useRenderToolCall({
    name: "render_form",
    description: "Render dynamic form",
    handler: async (toolCall: any) => {
      try {
        const { form_spec, form_id } = toolCall;
        
        const form = {
          id: form_id || `form_${Date.now()}`,
          spec: form_spec,
          timestamp: new Date().toISOString(),
          values: {}
        };
        
        setForms(prev => [...prev, form]);
        setActiveForm(form);
        
        return { rendered: true, form_id: form.id };
      } catch (error) {
        console.error("Form render error:", error);
        return { error: "Failed to render form" };
      }
    },
  });

  // Handle form submission
  const submitForm = useRenderToolCall({
    name: "submit_form",
    description: "Submit form data",
    handler: async (toolCall: any) => {
      try {
        const { form_id, values } = toolCall;
        
        // Update form with submitted values
        setForms(prev => 
          prev.map(form => 
            form.id === form_id 
              ? { ...form, values, submitted: true, submittedAt: new Date().toISOString() }
              : form
          )
        );
        
        // Clear active form if it's the submitted one
        if (activeForm?.id === form_id) {
          setActiveForm(null);
        }
        
        return { submitted: true };
      } catch (error) {
        console.error("Form submission error:", error);
        return { error: "Failed to submit form" };
      }
    },
  });

  // Update form values
  const updateFormValues = (formId: string, values: any) => {
    setForms(prev => 
      prev.map(form => 
        form.id === formId 
          ? { ...form, values: { ...form.values, ...values } }
          : form
      )
    );
  };

  return {
    renderForm,
    submitForm,
    forms,
    activeForm,
    setActiveForm,
    updateFormValues,
  };
}

export function useChartRenderer() {
  const [charts, setCharts] = useState<any[]>([]);
  const [chartData, setChartData] = useState<Record<string, any>>({});

  // Render charts
  const renderChart = useRenderToolCall({
    name: "render_chart",
    description: "Render data visualization",
    handler: async (toolCall: any) => {
      try {
        const { chart_spec, chart_id, data } = toolCall;
        
        const chart = {
          id: chart_id || `chart_${Date.now()}`,
          spec: chart_spec,
          timestamp: new Date().toISOString()
        };
        
        setCharts(prev => [...prev, chart]);
        if (data) {
          setChartData(prev => ({ ...prev, [chart.id]: data }));
        }
        
        return { rendered: true, chart_id: chart.id };
      } catch (error) {
        console.error("Chart render error:", error);
        return { error: "Failed to render chart" };
      }
    },
  });

  // Update chart data
  const updateChartData = useRenderToolCall({
    name: "update_chart_data",
    description: "Update chart data",
    handler: async (toolCall: any) => {
      try {
        const { chart_id, data } = toolCall;
        
        setChartData(prev => ({ ...prev, [chart_id]: data }));
        
        return { updated: true };
      } catch (error) {
        console.error("Chart data update error:", error);
        return { error: "Failed to update chart data" };
      }
    },
  });

  return {
    renderChart,
    updateChartData,
    charts,
    chartData,
  };
}

export function useTableRenderer() {
  const [tables, setTables] = useState<any[]>([]);
  const [tableData, setTableData] = useState<Record<string, any>>({});

  // Render tables
  const renderTable = useRenderToolCall({
    name: "render_table",
    description: "Render data table",
    handler: async (toolCall: any) => {
      try {
        const { table_spec, table_id, data } = toolCall;
        
        const table = {
          id: table_id || `table_${Date.now()}`,
          spec: table_spec,
          timestamp: new Date().toISOString()
        };
        
        setTables(prev => [...prev, table]);
        if (data) {
          setTableData(prev => ({ ...prev, [table.id]: data }));
        }
        
        return { rendered: true, table_id: table.id };
      } catch (error) {
        console.error("Table render error:", error);
        return { error: "Failed to render table" };
      }
    },
  });

  // Update table data
  const updateTableData = useRenderToolCall({
    name: "update_table_data",
    description: "Update table data",
    handler: async (toolCall: any) => {
      try {
        const { table_id, data } = toolCall;
        
        setTableData(prev => ({ ...prev, [table_id]: data }));
        
        return { updated: true };
      } catch (error) {
        console.error("Table data update error:", error);
        return { error: "Failed to update table data" };
      }
    },
  });

  return {
    renderTable,
    updateTableData,
    tables,
    tableData,
  };
}
