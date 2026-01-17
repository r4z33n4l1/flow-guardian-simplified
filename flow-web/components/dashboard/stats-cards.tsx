'use client';

import { useEffect, useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Brain, GitBranch, Lightbulb, Users, TrendingUp, Sparkles } from 'lucide-react';

interface Stats {
  sessions_count: number;
  learnings_count: number;
  team_learnings: number;
  top_tags: Array<{ tag: string; count: number }>;
}

function AnimatedCounter({ value, duration = 2000 }: { value: number; duration?: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;

    let start = 0;
    const end = value;
    if (end === 0) {
      setCount(0);
      return;
    }

    const incrementTime = duration / Math.min(end, 60);
    const step = Math.ceil(end / 60);

    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(start);
      }
    }, incrementTime);

    return () => clearInterval(timer);
  }, [value, duration, isInView]);

  return <span ref={ref}>{count.toLocaleString()}</span>;
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  gradient: string;
  glowColor: string;
  delay?: number;
}

function StatCard({ title, value, icon, gradient, glowColor, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, type: 'spring', stiffness: 200, damping: 20 }}
      whileHover={{ y: -4, scale: 1.02 }}
      className="group relative"
    >
      {/* Glow effect */}
      <div
        className="absolute -inset-0.5 rounded-2xl opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-500"
        style={{ background: glowColor }}
      />

      {/* Card - white with warm border on hover */}
      <div className="relative overflow-hidden rounded-2xl border border-[#E8E0D4] hover:border-orange-300 bg-white p-6 transition-colors duration-300 shadow-sm">
        <div className="relative flex items-start justify-between">
          <div className="space-y-3">
            <p className="text-sm font-medium text-[#6B6560] tracking-wide uppercase">
              {title}
            </p>
            <p className="text-4xl font-bold text-[#2D2A26] tracking-tight">
              <AnimatedCounter value={value} />
            </p>
          </div>

          {/* Icon with orange background */}
          <div
            className="p-3 rounded-xl"
            style={{ background: gradient }}
          >
            <div className="text-white">{icon}</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export function StatsCards() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
        const response = await fetch(`${apiUrl}/stats`);
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-36 rounded-2xl shimmer"
            style={{ animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Sessions"
        value={stats?.sessions_count || 0}
        icon={<GitBranch className="w-6 h-6" />}
        gradient="linear-gradient(135deg, #f97316 0%, #ea580c 100%)"
        glowColor="rgba(249, 115, 22, 0.2)"
        delay={0}
      />
      <StatCard
        title="Learnings"
        value={stats?.learnings_count || 0}
        icon={<Lightbulb className="w-6 h-6" />}
        gradient="linear-gradient(135deg, #f97316 0%, #ea580c 100%)"
        glowColor="rgba(249, 115, 22, 0.2)"
        delay={0.1}
      />
      <StatCard
        title="Team Insights"
        value={stats?.team_learnings || 0}
        icon={<Users className="w-6 h-6" />}
        gradient="linear-gradient(135deg, #f97316 0%, #ea580c 100%)"
        glowColor="rgba(249, 115, 22, 0.2)"
        delay={0.2}
      />
      <StatCard
        title="Active Tags"
        value={stats?.top_tags?.length || 0}
        icon={<TrendingUp className="w-6 h-6" />}
        gradient="linear-gradient(135deg, #f97316 0%, #ea580c 100%)"
        glowColor="rgba(249, 115, 22, 0.2)"
        delay={0.3}
      />
    </div>
  );
}

export function TopTagsCard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
        const response = await fetch(`${apiUrl}/stats`);
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const topTags = stats?.top_tags?.slice(0, 8) || [];
  const maxCount = topTags.length > 0 ? topTags[0].count : 1;

  // Orange-based color variations for tags
  const tagColors = [
    'from-orange-500 to-orange-600',
    'from-orange-500/80 to-orange-600/80',
    'from-orange-500/60 to-orange-600/60',
    'from-orange-500/50 to-orange-600/50',
    'from-orange-500/40 to-orange-600/40',
    'from-orange-500/30 to-orange-600/30',
    'from-orange-500/25 to-orange-600/25',
    'from-orange-500/20 to-orange-600/20',
  ];

  if (loading) {
    return (
      <div className="rounded-2xl border border-[#E8E0D4] bg-white p-6 shadow-sm">
        <div className="h-6 w-32 shimmer rounded mb-6" />
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-8 shimmer rounded" style={{ animationDelay: `${i * 0.1}s` }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="rounded-2xl border border-[#E8E0D4] hover:border-orange-200 bg-white p-6 transition-colors duration-300 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-6">
        <Sparkles className="w-5 h-5 text-orange-500" />
        <h3 className="text-lg font-semibold text-[#2D2A26]">Popular Tags</h3>
      </div>

      <div className="space-y-4">
        {topTags.length === 0 ? (
          <p className="text-[#6B6560] text-sm">No tags yet</p>
        ) : (
          topTags.map((tag, index) => (
            <motion.div
              key={tag.tag}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + index * 0.05 }}
              className="group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-[#6B6560] group-hover:text-[#2D2A26] transition-colors">
                  #{tag.tag}
                </span>
                <span className="text-xs font-mono text-[#6B6560]">
                  {tag.count.toLocaleString()}
                </span>
              </div>
              <div className="h-2 bg-[#F5F0E8] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(tag.count / maxCount) * 100}%` }}
                  transition={{ delay: 0.6 + index * 0.05, duration: 0.6, ease: 'easeOut' }}
                  className={`h-full rounded-full bg-gradient-to-r ${tagColors[index % tagColors.length]}`}
                />
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
}
