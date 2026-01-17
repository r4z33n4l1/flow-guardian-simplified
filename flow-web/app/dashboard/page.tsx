'use client';

import { motion } from 'framer-motion';
import { ArrowLeft, LayoutDashboard, Network, MessageSquare, Activity, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { StatsCards, TopTagsCard } from '@/components/dashboard/stats-cards';
import { ActivityTimeline } from '@/components/dashboard/activity-timeline';
import { ActivityChart, TagDistributionChart } from '@/components/dashboard/insights-chart';
import { TeamActivityWidget } from '@/components/team/team-feed';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-50 h-16 border-b border-[#fca311]/10 flex items-center justify-between px-6 bg-black/80 backdrop-blur-xl"
      >
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2 text-[#e5e5e5]/70 hover:text-[#fca311] hover:bg-[#fca311]/5">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
          </Link>
          <div className="w-px h-6 bg-[#fca311]/20" />
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-[#fca311]">
              <LayoutDashboard className="w-5 h-5 text-black" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Dashboard</h1>
              <p className="text-xs text-[#e5e5e5]/50">Real-time insights</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/graph">
            <Button variant="ghost" size="sm" className="gap-2 text-[#e5e5e5]/70 hover:text-[#fca311] hover:bg-[#fca311]/5">
              <Network className="w-4 h-4" />
              Knowledge Graph
            </Button>
          </Link>
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2 text-[#e5e5e5]/70 hover:text-[#fca311] hover:bg-[#fca311]/5">
              <MessageSquare className="w-4 h-4" />
              Chat
            </Button>
          </Link>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Stats Cards */}
        <section className="mb-10">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 mb-6"
          >
            <Sparkles className="w-5 h-5 text-[#fca311]" />
            <h2 className="text-xl font-semibold text-white">Overview</h2>
          </motion.div>
          <StatsCards />
        </section>

        {/* Charts Row */}
        <section className="mb-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ActivityChart />
          <TagDistributionChart />
        </section>

        {/* Activity and Tags Row */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Activity Timeline */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="rounded-2xl border border-[#fca311]/10 hover:border-[#fca311]/20 bg-[#14213d]/80 backdrop-blur-xl p-6 transition-colors duration-300"
            >
              <div className="flex items-center gap-2 mb-6">
                <Activity className="w-5 h-5 text-[#fca311]" />
                <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
              </div>
              <div className="max-h-[600px] overflow-y-auto pr-2">
                <ActivityTimeline />
              </div>
            </motion.div>
          </div>

          {/* Top Tags and Team Activity */}
          <div className="space-y-6">
            <TopTagsCard />
            <TeamActivityWidget />
          </div>
        </section>
      </main>
    </div>
  );
}
