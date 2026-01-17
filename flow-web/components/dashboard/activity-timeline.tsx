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
      <div className="absolute left-3 top-0 bottom-0 w-px bg-gradient-to-b from-orange-300 via-[#E8E0D4] to-transparent" />

      {/* Timeline dot */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: Math.min(index * 0.03, 0.3) + 0.1, type: 'spring' }}
        className={`absolute left-0 top-3 w-6 h-6 rounded-full flex items-center justify-center border-2 ${
          isSession
            ? 'bg-orange-50 border-orange-500'
            : 'bg-[#F5F0E8] border-[#E8E0D4]'
        }`}
      >
        {isSession ? (
          <GitBranch className="w-3 h-3 text-orange-500" />
        ) : (
          <Lightbulb className="w-3 h-3 text-[#6B6560]" />
        )}
      </motion.div>

      {/* Content */}
      <div
        className={`group rounded-xl border bg-white p-4 mb-3 transition-all cursor-pointer hover:bg-[#F5F0E8] ${
          isSession ? 'border-orange-200 hover:border-orange-300' : 'border-[#E8E0D4] hover:border-[#d4ccc0]'
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
                    ? 'bg-orange-50 text-orange-600 border-orange-200 text-xs font-medium'
                    : 'bg-[#F5F0E8] text-[#6B6560] border-[#E8E0D4] text-xs font-medium'
                }
              >
                {isSession ? 'Session' : 'Learning'}
              </Badge>
              <span className="text-xs text-[#6B6560] flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatTimeAgo(item.timestamp)}
              </span>
            </div>
            <p className="text-sm text-[#2D2A26] leading-relaxed line-clamp-2">
              {isSession ? data.summary : data.insight}
            </p>
          </div>
          <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0 text-[#6B6560] hover:text-orange-500">
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
              <div className="mt-3 pt-3 border-t border-[#E8E0D4]">
                {isSession && data.branch && (
                  <div className="flex items-center gap-2 text-xs text-[#6B6560] mb-2">
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
                        className="bg-orange-50 text-orange-600 border-orange-200 text-xs"
                      >
                        #{tag}
                      </Badge>
                    ))}
                    {data.tags.length > 5 && (
                      <Badge variant="secondary" className="bg-[#F5F0E8] text-[#6B6560] text-xs">
                        +{data.tags.length - 5} more
                      </Badge>
                    )}
                  </div>
                )}
                <p className="text-xs text-[#9a918a] mt-3">
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
      // Use index to ensure unique keys even if IDs are duplicated
      const combined: TimelineItem[] = [
        ...sessions.map((s, idx) => ({
          id: `session-${s.id || s.timestamp}-${idx}`,
          type: 'session' as const,
          timestamp: s.timestamp,
          data: s,
        })),
        ...learnings.map((l, idx) => ({
          id: `learning-${l.id || l.timestamp}-${idx}`,
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
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[#F5F0E8] flex items-center justify-center">
          <Lightbulb className="w-8 h-8 text-orange-300" />
        </div>
        <p className="text-[#2D2A26] font-medium">No activity yet</p>
        <p className="text-[#6B6560] text-sm mt-1">Sessions and learnings will appear here</p>
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
          className="text-[#6B6560] hover:text-orange-500"
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
            className="border-[#E8E0D4] text-[#6B6560] hover:text-orange-500 hover:border-orange-300 hover:bg-orange-50"
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
