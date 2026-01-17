'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, PieChart as PieChartIcon } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface Learning {
  id: string;
  timestamp: string;
  tags: string[];
}

interface Session {
  id: string;
  timestamp: string;
}

// Generate activity data from sessions and learnings
function generateActivityData(sessions: Session[], learnings: Learning[]) {
  const days = 7;
  const data = [];
  const now = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const sessionsCount = sessions.filter((s) => s.timestamp.startsWith(dateStr)).length;
    const learningsCount = learnings.filter((l) => l.timestamp.startsWith(dateStr)).length;

    data.push({
      date: date.toLocaleDateString('en-US', { weekday: 'short' }),
      sessions: sessionsCount,
      learnings: learningsCount,
    });
  }

  return data;
}

// Generate tag distribution data
function generateTagData(learnings: Learning[]) {
  const tagCounts: Record<string, number> = {};

  learnings.forEach((l) => {
    (l.tags || []).forEach((tag) => {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    });
  });

  return Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, value]) => ({ name, value }));
}

// Gold-centric color palette
const COLORS = [
  '#fca311', // gold
  '#d4a017', // darker gold
  '#e5e5e5', // alabaster
  '#ffffff', // white
  '#fca311cc', // gold 80%
  '#d4a017cc', // darker gold 80%
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#14213d]/95 backdrop-blur-xl border border-[#fca311]/20 rounded-xl p-3 shadow-xl">
        <p className="text-[#e5e5e5]/60 text-xs mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-[#e5e5e5]">{entry.name}:</span>
            <span className="text-white font-medium">{entry.value}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function ActivityChart() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';

        const [sessionsRes, learningsRes] = await Promise.all([
          fetch(`${apiUrl}/sessions?limit=100`),
          fetch(`${apiUrl}/learnings?limit=100`),
        ]);

        const sessions = sessionsRes.ok ? (await sessionsRes.json()).sessions || [] : [];
        const learnings = learningsRes.ok ? (await learningsRes.json()).learnings || [] : [];

        setData(generateActivityData(sessions, learnings));
      } catch (err) {
        console.error('Failed to fetch chart data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl border border-[#fca311]/10 bg-[#14213d]/80 backdrop-blur-xl p-6">
        <div className="h-6 w-40 shimmer rounded mb-4" />
        <div className="h-64 shimmer rounded-xl" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-[#fca311]/10 hover:border-[#fca311]/20 bg-[#14213d]/80 backdrop-blur-xl p-6 transition-colors duration-300"
    >
      <div className="flex items-center gap-2 mb-6">
        <TrendingUp className="w-5 h-5 text-[#fca311]" />
        <h3 className="text-lg font-semibold text-white">Activity (7 days)</h3>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorSessions" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fca311" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#fca311" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorLearnings" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#e5e5e5" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#e5e5e5" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(252, 163, 17, 0.08)" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#e5e5e5"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              opacity={0.5}
            />
            <YAxis
              stroke="#e5e5e5"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              opacity={0.5}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="sessions"
              stroke="#fca311"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorSessions)"
              name="Sessions"
            />
            <Area
              type="monotone"
              dataKey="learnings"
              stroke="#e5e5e5"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorLearnings)"
              name="Learnings"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center gap-8 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#fca311]" />
          <span className="text-sm text-[#e5e5e5]/70">Sessions</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#e5e5e5]" />
          <span className="text-sm text-[#e5e5e5]/70">Learnings</span>
        </div>
      </div>
    </motion.div>
  );
}

export function TagDistributionChart() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
        const res = await fetch(`${apiUrl}/learnings?limit=100`);
        if (res.ok) {
          const { learnings } = await res.json();
          setData(generateTagData(learnings || []));
        }
      } catch (err) {
        console.error('Failed to fetch tag data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl border border-[#fca311]/10 bg-[#14213d]/80 backdrop-blur-xl p-6">
        <div className="h-6 w-40 shimmer rounded mb-4" />
        <div className="h-48 shimmer rounded-xl" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-[#fca311]/10 bg-[#14213d]/80 backdrop-blur-xl p-6 h-[340px] flex flex-col items-center justify-center"
      >
        <PieChartIcon className="w-12 h-12 text-[#e5e5e5]/20 mb-3" />
        <p className="text-[#e5e5e5]/60 font-medium">No tag data available</p>
        <p className="text-[#e5e5e5]/40 text-sm mt-1">Tags will appear as you add learnings</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="rounded-2xl border border-[#fca311]/10 hover:border-[#fca311]/20 bg-[#14213d]/80 backdrop-blur-xl p-6 transition-colors duration-300"
    >
      <div className="flex items-center gap-2 mb-6">
        <PieChartIcon className="w-5 h-5 text-[#fca311]" />
        <h3 className="text-lg font-semibold text-white">Tag Distribution</h3>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
              stroke="#000000"
              strokeWidth={2}
            >
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                  className="transition-opacity hover:opacity-80"
                />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-[#14213d]/95 backdrop-blur-xl border border-[#fca311]/20 rounded-xl p-3 shadow-xl">
                      <div className="flex items-center gap-2">
                        <span className="text-[#e5e5e5]">#{payload[0].name}:</span>
                        <span className="text-white font-medium">{payload[0].value}</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mt-4">
        {data.map((entry, index) => (
          <div key={entry.name} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <span className="text-xs text-[#e5e5e5]/70">#{entry.name}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
