'use client';

import { useEffect, useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import Link from 'next/link';
import {
  Brain,
  Network,
  LayoutDashboard,
  MessageSquare,
  Sparkles,
  GitBranch,
  Lightbulb,
  Users,
  ArrowRight,
  Zap,
  ChevronDown,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Stats {
  sessions_count: number;
  learnings_count: number;
  team_learnings: number;
}

function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;

    const duration = 2000;
    const steps = Math.min(value, 60);
    const increment = value / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value, isInView]);

  return (
    <span ref={ref}>
      {count.toLocaleString()}
      {suffix}
    </span>
  );
}

// Floating particles effect
function FloatingParticles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(30)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-purple-400/30 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -100, 0],
            opacity: [0, 0.8, 0],
            scale: [0, 1, 0],
          }}
          transition={{
            duration: 4 + Math.random() * 4,
            delay: Math.random() * 4,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}

// Aurora gradient background
function AuroraBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Primary aurora */}
      <motion.div
        animate={{
          x: [0, 50, 0],
          y: [0, 30, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        className="absolute -top-1/2 -left-1/4 w-[150%] h-[150%] opacity-40"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(168, 85, 247, 0.3) 0%, transparent 60%)',
        }}
      />
      {/* Secondary aurora */}
      <motion.div
        animate={{
          x: [0, -30, 0],
          y: [0, -50, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
        className="absolute -bottom-1/4 -right-1/4 w-[120%] h-[120%] opacity-30"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(99, 102, 241, 0.3) 0%, transparent 50%)',
        }}
      />
      {/* Cyan accent */}
      <motion.div
        animate={{
          x: [0, 40, 0],
          y: [0, -40, 0],
        }}
        transition={{ duration: 15, repeat: Infinity, ease: 'linear' }}
        className="absolute top-1/3 right-1/4 w-96 h-96 opacity-20"
        style={{
          background: 'radial-gradient(circle, rgba(6, 182, 212, 0.4) 0%, transparent 60%)',
        }}
      />
    </div>
  );
}

export function HeroSection() {
  const [stats, setStats] = useState<Stats | null>(null);

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
        // Silently fail - stats are optional
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-background px-4">
      <AuroraBackground />
      <FloatingParticles />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '64px 64px',
        }}
      />

      {/* Noise texture */}
      <div
        className="absolute inset-0 opacity-[0.015] pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />

      {/* Content */}
      <div className="relative z-10 text-center max-w-5xl mx-auto">
        {/* Logo/Icon */}
        <motion.div
          initial={{ opacity: 0, scale: 0.5, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.6, type: 'spring' }}
          className="mb-10"
        >
          <div className="relative inline-block">
            {/* Outer glow ring */}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              className="absolute -inset-4 rounded-3xl opacity-60"
              style={{
                background: 'conic-gradient(from 0deg, transparent, rgba(168, 85, 247, 0.4), transparent, rgba(99, 102, 241, 0.4), transparent)',
              }}
            />
            {/* Icon container */}
            <div className="relative bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-2xl">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20" />
              <Brain className="relative w-14 h-14 text-white" />
            </div>
          </div>
        </motion.div>

        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium">
            <Sparkles className="w-4 h-4" />
            AI-Powered Team Memory
          </span>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-5xl sm:text-6xl md:text-8xl font-bold mb-6 tracking-tight"
        >
          <span className="bg-gradient-to-b from-white via-white to-slate-400 bg-clip-text text-transparent">
            Flow
          </span>
          <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
            {' '}Guardian
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-lg sm:text-xl md:text-2xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed font-light"
        >
          Capture, connect, and recall your development context.
          <br className="hidden sm:block" />
          <span className="text-slate-500">Never lose an insight again.</span>
        </motion.p>

        {/* Live Stats */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex justify-center gap-6 sm:gap-12 md:gap-16 mb-12"
          >
            <StatBadge
              value={stats.sessions_count}
              label="Sessions"
              icon={<GitBranch className="w-4 h-4" />}
              gradient="from-indigo-500 to-purple-500"
            />
            <StatBadge
              value={stats.learnings_count}
              label="Learnings"
              icon={<Lightbulb className="w-4 h-4" />}
              gradient="from-cyan-500 to-emerald-500"
            />
            <StatBadge
              value={stats.team_learnings}
              label="Team Insights"
              icon={<Users className="w-4 h-4" />}
              gradient="from-purple-500 to-pink-500"
            />
          </motion.div>
        )}

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center mb-20"
        >
          <Link href="/graph">
            <Button
              size="lg"
              className="group gap-3 h-14 px-8 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0 shadow-lg shadow-purple-500/25 text-base font-medium rounded-xl transition-all hover:shadow-purple-500/40 hover:scale-105"
            >
              <Network className="w-5 h-5" />
              Explore Knowledge Graph
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button
              size="lg"
              variant="outline"
              className="gap-3 h-14 px-8 border-slate-700 text-white hover:bg-white/5 hover:border-slate-600 text-base font-medium rounded-xl transition-all hover:scale-105"
            >
              <LayoutDashboard className="w-5 h-5" />
              View Dashboard
            </Button>
          </Link>
        </motion.div>

        {/* Feature cards */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto"
        >
          <FeatureCard
            icon={<Network className="w-6 h-6" />}
            title="Knowledge Graph"
            description="Visualize connections between sessions, learnings, and concepts"
            gradient="from-indigo-500 to-purple-500"
            delay={0.8}
          />
          <FeatureCard
            icon={<Sparkles className="w-6 h-6" />}
            title="AI Suggestions"
            description="Proactive insights based on your development patterns"
            gradient="from-purple-500 to-pink-500"
            delay={0.9}
          />
          <FeatureCard
            icon={<Zap className="w-6 h-6" />}
            title="Real-time Sync"
            description="Auto-capture from Claude Code sessions instantly"
            gradient="from-cyan-500 to-emerald-500"
            delay={1.0}
          />
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="flex flex-col items-center gap-2"
        >
          <span className="text-xs text-slate-600 uppercase tracking-widest">Scroll</span>
          <ChevronDown className="w-5 h-5 text-slate-600" />
        </motion.div>
      </motion.div>
    </div>
  );
}

function StatBadge({
  value,
  label,
  icon,
  gradient,
}: {
  value: number;
  label: string;
  icon: React.ReactNode;
  gradient: string;
}) {
  return (
    <div className="text-center">
      <div className={`text-3xl sm:text-4xl md:text-5xl font-bold bg-gradient-to-r ${gradient} bg-clip-text text-transparent`}>
        <AnimatedCounter value={value} />
      </div>
      <div className="flex items-center justify-center gap-1.5 mt-2 text-slate-500 text-sm">
        {icon}
        {label}
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  gradient,
  delay,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  gradient: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -6, scale: 1.02 }}
      className="group relative"
    >
      {/* Glow effect on hover */}
      <div className={`absolute -inset-0.5 rounded-2xl bg-gradient-to-r ${gradient} opacity-0 group-hover:opacity-30 blur-xl transition-opacity duration-500`} />

      {/* Card */}
      <div className="relative p-6 rounded-2xl border border-white/[0.08] bg-slate-900/60 backdrop-blur-xl overflow-hidden">
        {/* Gradient accent at top */}
        <div className={`absolute top-0 left-0 right-0 h-px bg-gradient-to-r ${gradient} opacity-50`} />

        {/* Icon */}
        <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${gradient} mb-4`}>
          <div className="text-white">{icon}</div>
        </div>

        <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
        <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}
