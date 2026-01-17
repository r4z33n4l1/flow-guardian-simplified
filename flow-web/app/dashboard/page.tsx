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
    <div className="min-h-screen bg-[#FAF8F5]">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-50 h-16 border-b border-[#E8E0D4] flex items-center justify-between px-6 bg-[#FAF8F5]/80 backdrop-blur-xl"
      >
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
          </Link>
          <div className="w-px h-6 bg-[#E8E0D4]" />
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-orange-500">
              <LayoutDashboard className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-[#2D2A26]">Dashboard</h1>
              <p className="text-xs text-[#6B6560]">Real-time insights</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/graph">
            <Button variant="ghost" size="sm" className="gap-2 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50">
              <Network className="w-4 h-4" />
              Knowledge Graph
            </Button>
          </Link>
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50">
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
            <Sparkles className="w-5 h-5 text-orange-500" />
            <h2 className="text-xl font-semibold text-[#2D2A26]">Overview</h2>
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
              className="rounded-2xl border border-[#E8E0D4] hover:border-orange-200 bg-white p-6 transition-colors duration-300 shadow-sm"
            >
              <div className="flex items-center gap-2 mb-6">
                <Activity className="w-5 h-5 text-orange-500" />
                <h3 className="text-lg font-semibold text-[#2D2A26]">Recent Activity</h3>
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
