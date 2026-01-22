'use client';

import { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { TrendingUp, TrendingDown, Users, Target, DollarSign, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  className?: string;
}

function MetricCard({ title, value, change, icon, className }: MetricCardProps) {
  return (
    <div className={cn("bg-white rounded-lg border border-gray-200 p-4", className)}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change !== undefined && (
            <div className={cn(
              "flex items-center gap-1 text-sm",
              change >= 0 ? "text-green-600" : "text-red-600"
            )}>
              {change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>{Math.abs(change)}%</span>
            </div>
          )}
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          {icon}
        </div>
      </div>
    </div>
  );
}

interface AnalyticsDashboardProps {
  className?: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export function AnalyticsDashboard({ className }: AnalyticsDashboardProps) {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // Simulate loading analytics data
    setIsLoading(true);
    
    // Mock data - in production, fetch from API
    setTimeout(() => {
      setData({
        metrics: {
          totalProspects: 1247,
          conversionRate: 18.5,
          totalRevenue: 125000,
          activeAgents: 3
        },
        conversionTrend: [
          { date: 'Week 1', rate: 15.2, prospects: 180 },
          { date: 'Week 2', rate: 16.8, prospects: 210 },
          { date: 'Week 3', rate: 17.5, prospects: 195 },
          { date: 'Week 4', rate: 18.5, prospects: 225 }
        ],
        sourceBreakdown: [
          { name: 'Search', value: 35 },
          { name: 'Outreach', value: 28 },
          { name: 'Referral', value: 22 },
          { name: 'Direct', value: 15 }
        ],
        agentPerformance: [
          { name: 'Business Growth', executions: 450, successRate: 94 },
          { name: 'Performance', executions: 280, successRate: 97 },
          { name: 'Finance', executions: 120, successRate: 99 }
        ],
        recentActivity: [
          { time: '2 min ago', action: 'Prospect converted', details: 'ABC Corp' },
          { time: '15 min ago', action: 'Pitch generated', details: 'XYZ Industries' },
          { time: '1 hour ago', action: 'Outreach sent', details: '25 messages' },
          { time: '2 hours ago', action: 'Report generated', details: 'Weekly summary' }
        ]
      });
      setIsLoading(false);
    }, 1000);
  }, [timeRange]);

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center h-64", className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className={cn("analytics-dashboard space-y-6", className)}>
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Analytics Dashboard</h2>
        <div className="flex gap-2">
          {(['7d', '30d', '90d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={cn(
                "px-3 py-1 text-sm rounded-lg transition-colors",
                timeRange === range
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Prospects"
          value={data.metrics.totalProspects.toLocaleString()}
          change={12}
          icon={<Users className="w-6 h-6 text-blue-600" />}
        />
        <MetricCard
          title="Conversion Rate"
          value={`${data.metrics.conversionRate}%`}
          change={8}
          icon={<Target className="w-6 h-6 text-green-600" />}
        />
        <MetricCard
          title="Total Revenue"
          value={`$${(data.metrics.totalRevenue / 1000).toFixed(0)}K`}
          change={15}
          icon={<DollarSign className="w-6 h-6 text-yellow-600" />}
        />
        <MetricCard
          title="Active Agents"
          value={data.metrics.activeAgents}
          icon={<Activity className="w-6 h-6 text-purple-600" />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion Trend */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversion Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={data.conversionTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="rate" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Conversion Rate (%)"
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="prospects" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Prospects"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Source Breakdown */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Sources</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data.sourceBreakdown}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data.sourceBreakdown.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agent Performance */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Performance</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data.agentPerformance} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" width={120} />
            <Tooltip />
            <Legend />
            <Bar dataKey="executions" fill="#3B82F6" name="Executions" />
            <Bar dataKey="successRate" fill="#10B981" name="Success Rate (%)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {data.recentActivity.map((activity: any, index: number) => (
            <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <div>
                <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                <p className="text-xs text-gray-500">{activity.details}</p>
              </div>
              <span className="text-xs text-gray-400">{activity.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AnalyticsDashboard;
