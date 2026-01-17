'use client';

import { Node } from '@xyflow/react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Clock, GitBranch, Hash, Lightbulb, Users, AlertCircle, ExternalLink, Copy, Check } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

interface NodeDetailsProps {
  node: Node | null;
  onClose: () => void;
}

const TYPE_CONFIG = {
  session: {
    gradient: 'from-indigo-500 to-purple-500',
    bgGradient: 'from-indigo-500/10 to-purple-500/10',
    border: 'border-indigo-500/30',
    text: 'text-indigo-400',
    icon: GitBranch,
    label: 'Session'
  },
  learning: {
    gradient: 'from-cyan-500 to-emerald-500',
    bgGradient: 'from-cyan-500/10 to-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    icon: Lightbulb,
    label: 'Learning'
  },
  tag: {
    gradient: 'from-purple-500 to-pink-500',
    bgGradient: 'from-purple-500/10 to-pink-500/10',
    border: 'border-purple-500/30',
    text: 'text-purple-400',
    icon: Hash,
    label: 'Tag'
  },
  issue: {
    gradient: 'from-amber-500 to-red-500',
    bgGradient: 'from-amber-500/10 to-red-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    icon: AlertCircle,
    label: 'Issue'
  },
};

export function NodeDetails({ node, onClose }: NodeDetailsProps) {
  const [copied, setCopied] = useState(false);

  if (!node) return null;

  const data = node.data as any;
  const type = node.type as keyof typeof TYPE_CONFIG;
  const config = TYPE_CONFIG[type] || TYPE_CONFIG.learning;
  const Icon = config.icon;

  const formatTimestamp = (ts: string) => {
    if (!ts) return 'Unknown';
    try {
      const date = new Date(ts);
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return ts;
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getContent = () => {
    if (type === 'session') return data.summary || data.label;
    if (type === 'learning') return data.insight || data.label;
    if (type === 'tag') return `#${data.tag || data.label}`;
    return data.label;
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 320 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 320 }}
        transition={{ type: 'spring', stiffness: 400, damping: 35 }}
        className="absolute top-0 right-0 w-[360px] h-full z-20 overflow-hidden flex flex-col"
      >
        {/* Glass background */}
        <div className="absolute inset-0 bg-slate-900/95 backdrop-blur-xl border-l border-white/[0.08]" />

        {/* Gradient accent at top */}
        <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${config.gradient}`} />

        {/* Content */}
        <div className="relative flex flex-col h-full">
          {/* Header */}
          <div className="p-5 border-b border-white/[0.08]">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${config.gradient} shadow-lg`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <Badge
                    variant="outline"
                    className={`bg-gradient-to-r ${config.bgGradient} ${config.text} ${config.border} font-medium`}
                  >
                    {config.label}
                  </Badge>
                  {data.shared && (
                    <div className="flex items-center gap-1 mt-1.5 text-xs text-emerald-400">
                      <Users className="w-3 h-3" />
                      <span>Shared with team</span>
                    </div>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="h-8 w-8 text-slate-500 hover:text-white hover:bg-white/10 rounded-lg"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            {/* Title/Label */}
            <div>
              <h3 className="text-xl font-semibold text-white leading-snug">
                {data.label}
              </h3>
            </div>

            {/* Session Details */}
            {type === 'session' && (
              <>
                {data.branch && (
                  <div className="space-y-2">
                    <div className="text-xs text-slate-500 uppercase tracking-wider font-medium">Branch</div>
                    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r ${config.bgGradient} border ${config.border}`}>
                      <GitBranch className={`w-4 h-4 ${config.text}`} />
                      <code className="text-slate-200 text-sm font-mono">{data.branch}</code>
                    </div>
                  </div>
                )}
                {data.summary && (
                  <div className="space-y-2">
                    <div className="text-xs text-slate-500 uppercase tracking-wider font-medium">Summary</div>
                    <p className="text-slate-300 text-sm leading-relaxed">{data.summary}</p>
                  </div>
                )}
              </>
            )}

            {/* Learning Details */}
            {type === 'learning' && (
              <>
                {data.insight && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-slate-500 uppercase tracking-wider font-medium">Insight</div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(data.insight)}
                        className="h-6 px-2 text-xs text-slate-500 hover:text-white"
                      >
                        {copied ? (
                          <>
                            <Check className="w-3 h-3 mr-1" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3 mr-1" />
                            Copy
                          </>
                        )}
                      </Button>
                    </div>
                    <p className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                      {data.insight}
                    </p>
                  </div>
                )}
                {data.tags && data.tags.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs text-slate-500 uppercase tracking-wider font-medium">Tags</div>
                    <div className="flex flex-wrap gap-2">
                      {data.tags.map((tag: string) => (
                        <Badge
                          key={tag}
                          variant="secondary"
                          className="bg-violet-500/15 text-violet-300 border border-violet-500/30 text-xs hover:bg-violet-500/25 cursor-pointer transition-colors"
                        >
                          #{tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Tag Details */}
            {type === 'tag' && (
              <div className="space-y-3">
                <div className={`text-3xl font-bold bg-gradient-to-r ${config.gradient} bg-clip-text text-transparent`}>
                  #{data.tag || data.label}
                </div>
                <p className="text-slate-500 text-sm">
                  This tag connects related learnings and concepts in your knowledge graph.
                </p>
              </div>
            )}

            {/* Timestamp */}
            {data.timestamp && (
              <div className="space-y-2">
                <div className="text-xs text-slate-500 uppercase tracking-wider font-medium">Created</div>
                <div className="flex items-center gap-2 text-slate-400 text-sm">
                  <Clock className="w-4 h-4 text-slate-500" />
                  {formatTimestamp(data.timestamp)}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-white/[0.08] bg-slate-900/50">
            <p className="text-[11px] text-slate-600 text-center">
              Drag nodes to rearrange • Scroll to zoom
            </p>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
