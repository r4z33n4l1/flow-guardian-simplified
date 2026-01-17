'use client';

import { useState } from 'react';
import { Node } from '@xyflow/react';
import { KnowledgeGraph } from '@/components/graph/knowledge-graph';
import { NodeDetails } from '@/components/graph/node-details';
import { motion } from 'framer-motion';
import { ArrowLeft, Network, LayoutDashboard, MessageSquare, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function GraphPage() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  return (
    <div className="h-screen w-screen bg-background flex flex-col overflow-hidden">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="h-16 border-b border-white/[0.08] flex items-center justify-between px-6 bg-slate-900/50 backdrop-blur-xl"
      >
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2 text-slate-400 hover:text-white hover:bg-white/10">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
          </Link>
          <div className="w-px h-6 bg-white/10" />
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500">
              <Network className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Knowledge Graph</h1>
              <p className="text-xs text-slate-500">Visualize your AI memory</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="gap-2 text-slate-400 hover:text-white hover:bg-white/10">
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </Button>
          </Link>
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2 text-slate-400 hover:text-white hover:bg-white/10">
              <MessageSquare className="w-4 h-4" />
              Chat
            </Button>
          </Link>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="flex-1 relative overflow-hidden">
        <KnowledgeGraph onNodeSelect={setSelectedNode} />
        <NodeDetails node={selectedNode} onClose={() => setSelectedNode(null)} />
      </div>
    </div>
  );
}
