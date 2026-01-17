'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GitBranch, Lightbulb, Clock, ChevronDown, ChevronUp, Loader2, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface Session {
  id: string;
  timestamp: string;
  branch: string;
  summary: string;
}

interface Learning {
  id: string;
  timestamp: string;
  insight: string;
  tags: string[];
  shared?: boolean;
}

type TimelineItem = {
  id: string;
  type: 'session' | 'learning';
  timestamp: string;
  data: Session | Learning;
};

function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString();
}

function TimelineItemCard({ item, index }: { item: TimelineItem; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const isSession = item.type === 'session';
  const data = item.data as any;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: Math.min(index * 0.03, 0.3) }}
      className="relative pl-8"
    >
      {/* Timeline line */}
      <div className="absolute left-3 top-0 bottom-0 w-px bg-gradient-to-b from-slate-700 via-slate-800 to-transparent" />

      {/* Timeline dot */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: Math.min(index * 0.03, 0.3) + 0.1, type: 'spring' }}
        className={`absolute left-0 top-3 w-6 h-6 rounded-full flex items-center justify-center border-2 ${
          isSession
            ? 'bg-indigo-500/20 border-indigo-500'
            : 'bg-emerald-500/20 border-emerald-500'
        }`}
      >
        {isSession ? (
          <GitBranch className="w-3 h-3 text-indigo-400" />
        ) : (
          <Lightbulb className="w-3 h-3 text-emerald-400" />
        )}
      </motion.div>

      {/* Content */}
      <div
        className={`group rounded-xl border bg-slate-900/40 backdrop-blur p-4 mb-3 transition-all cursor-pointer hover:bg-slate-800/50 ${
          isSession ? 'border-indigo-500/20 hover:border-indigo-500/40' : 'border-emerald-500/20 hover:border-emerald-500/40'
        }`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge
                variant="outline"
                className={
                  isSession
                    ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30 text-xs font-medium'
                    : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 text-xs font-medium'
                }
              >
                {isSession ? 'Session' : 'Learning'}
              </Badge>
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatTimeAgo(item.timestamp)}
              </span>
            </div>
            <p className="text-sm text-slate-200 leading-relaxed line-clamp-2">
              {isSession ? data.summary : data.insight}
            </p>
          </div>
          <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0 text-slate-500">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="mt-3 pt-3 border-t border-slate-700/50">
                {isSession && data.branch && (
                  <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                    <GitBranch className="w-3 h-3" />
                    <span className="font-mono">{data.branch}</span>
                  </div>
                )}
                {!isSession && data.tags && data.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {data.tags.slice(0, 5).map((tag: string) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="bg-violet-500/15 text-violet-300 border-violet-500/30 text-xs"
                      >
                        #{tag}
                      </Badge>
                    ))}
                    {data.tags.length > 5 && (
                      <Badge variant="secondary" className="bg-slate-700/50 text-slate-400 text-xs">
                        +{data.tags.length - 5} more
                      </Badge>
                    )}
                  </div>
                )}
                <p className="text-xs text-slate-500 mt-3">
                  {new Date(item.timestamp).toLocaleString()}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

interface ActivityTimelineProps {
  initialLimit?: number;
}

export function ActivityTimeline({ initialLimit = 10 }: ActivityTimelineProps) {
  const [items, setItems] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);

  const fetchActivity = useCallback(async (pageNum: number, append: boolean = false) => {
    try {
      if (append) setLoadingMore(true);
      else setLoading(true);

      const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
      const limit = initialLimit;

      // Fetch sessions and learnings with pagination
      const [sessionsRes, learningsRes] = await Promise.all([
        fetch(`${apiUrl}/sessions?limit=${limit}&page=${pageNum}`),
        fetch(`${apiUrl}/learnings?limit=${limit}&page=${pageNum}`),
      ]);

      const sessionsData = sessionsRes.ok ? await sessionsRes.json() : { sessions: [], total: 0 };
      const learningsData = learningsRes.ok ? await learningsRes.json() : { learnings: [], total: 0 };

      const sessions: Session[] = sessionsData.sessions || [];
      const learnings: Learning[] = learningsData.learnings || [];

      // Combine and sort by timestamp
      const combined: TimelineItem[] = [
        ...sessions.map((s) => ({
          id: s.id || `session-${s.timestamp}`,
          type: 'session' as const,
          timestamp: s.timestamp,
          data: s,
        })),
        ...learnings.map((l) => ({
          id: l.id || `learning-${l.timestamp}`,
          type: 'learning' as const,
          timestamp: l.timestamp,
          data: l,
        })),
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      // Check if there's more data
      const totalItems = Math.max(sessionsData.total || 0, learningsData.total || 0);
      setHasMore(pageNum * limit < totalItems);

      if (append) {
        setItems((prev) => {
          const existingIds = new Set(prev.map((i) => i.id));
          const newItems = combined.filter((i) => !existingIds.has(i.id));
          return [...prev, ...newItems];
        });
      } else {
        setItems(combined);
      }
    } catch (err) {
      console.error('Failed to fetch activity:', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [initialLimit]);

  useEffect(() => {
    fetchActivity(1);
  }, [fetchActivity]);

  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchActivity(nextPage, true);
  };

  const refresh = () => {
    setPage(1);
    fetchActivity(1);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-24 rounded-xl shimmer ml-8"
            style={{ animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-800/50 flex items-center justify-center">
          <Lightbulb className="w-8 h-8 text-slate-600" />
        </div>
        <p className="text-slate-400 font-medium">No activity yet</p>
        <p className="text-slate-600 text-sm mt-1">Sessions and learnings will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {/* Refresh button */}
      <div className="flex justify-end mb-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={refresh}
          className="text-slate-500 hover:text-slate-300"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Timeline items */}
      <AnimatePresence mode="popLayout">
        {items.map((item, index) => (
          <TimelineItemCard key={item.id} item={item} index={index} />
        ))}
      </AnimatePresence>

      {/* Load more button */}
      {hasMore && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="pt-4 flex justify-center"
        >
          <Button
            variant="outline"
            size="sm"
            onClick={loadMore}
            disabled={loadingMore}
            className="border-slate-700 text-slate-400 hover:text-white hover:bg-slate-800"
          >
            {loadingMore ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              'Load more'
            )}
          </Button>
        </motion.div>
      )}
    </div>
  );
}
