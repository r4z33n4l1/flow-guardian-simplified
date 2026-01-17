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

      {/* Card */}
      <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-slate-900/60 backdrop-blur-xl p-6">
        {/* Gradient accent */}
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{ background: gradient }}
        />

        {/* Animated gradient line */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: delay + 0.4, duration: 0.8, ease: 'easeOut' }}
          className="absolute bottom-0 left-0 right-0 h-[2px]"
          style={{ background: gradient, transformOrigin: 'left' }}
        />

        <div className="relative flex items-start justify-between">
          <div className="space-y-3">
            <p className="text-sm font-medium text-slate-400 tracking-wide uppercase">
              {title}
            </p>
            <p className="text-4xl font-bold text-white tracking-tight">
              <AnimatedCounter value={value} />
            </p>
          </div>

          {/* Icon with gradient background */}
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
        gradient="linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)"
        glowColor="rgba(99, 102, 241, 0.3)"
        delay={0}
      />
      <StatCard
        title="Learnings"
        value={stats?.learnings_count || 0}
        icon={<Lightbulb className="w-6 h-6" />}
        gradient="linear-gradient(135deg, #06b6d4 0%, #10b981 100%)"
        glowColor="rgba(6, 182, 212, 0.3)"
        delay={0.1}
      />
      <StatCard
        title="Team Insights"
        value={stats?.team_learnings || 0}
        icon={<Users className="w-6 h-6" />}
        gradient="linear-gradient(135deg, #a855f7 0%, #ec4899 100%)"
        glowColor="rgba(168, 85, 247, 0.3)"
        delay={0.2}
      />
      <StatCard
        title="Active Tags"
        value={stats?.top_tags?.length || 0}
        icon={<TrendingUp className="w-6 h-6" />}
        gradient="linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)"
        glowColor="rgba(245, 158, 11, 0.3)"
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

  const tagColors = [
    'from-violet-500 to-purple-500',
    'from-cyan-500 to-blue-500',
    'from-emerald-500 to-teal-500',
    'from-amber-500 to-orange-500',
    'from-pink-500 to-rose-500',
    'from-indigo-500 to-violet-500',
    'from-teal-500 to-cyan-500',
    'from-orange-500 to-red-500',
  ];

  if (loading) {
    return (
      <div className="rounded-2xl border border-white/[0.08] bg-slate-900/60 backdrop-blur-xl p-6">
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
      className="rounded-2xl border border-white/[0.08] bg-slate-900/60 backdrop-blur-xl p-6"
    >
      <div className="flex items-center gap-2 mb-6">
        <Sparkles className="w-5 h-5 text-amber-400" />
        <h3 className="text-lg font-semibold text-white">Popular Tags</h3>
      </div>

      <div className="space-y-4">
        {topTags.length === 0 ? (
          <p className="text-slate-500 text-sm">No tags yet</p>
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
                <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                  #{tag.tag}
                </span>
                <span className="text-xs font-mono text-slate-500">
                  {tag.count.toLocaleString()}
                </span>
              </div>
              <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
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
