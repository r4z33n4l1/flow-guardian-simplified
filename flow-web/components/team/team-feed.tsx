'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Lightbulb, Clock, Share2, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface TeamLearning {
  id: string;
  insight: string;
  tags: string[];
  timestamp: string;
  shared?: boolean;
  author?: string;
}

// Generate gradient avatar colors based on string - gold variations
function stringToGradient(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const gradients = [
    'from-[#fca311] to-[#d4a017]',
    'from-[#fca311]/90 to-[#d4a017]/90',
    'from-[#fca311]/80 to-[#d4a017]/80',
    'from-[#d4a017] to-[#fca311]',
    'from-[#fca311]/70 to-[#d4a017]/70',
    'from-[#d4a017]/90 to-[#fca311]/90',
    'from-[#fca311]/85 to-[#d4a017]/85',
    'from-[#d4a017]/80 to-[#fca311]/80',
  ];
  return gradients[Math.abs(hash) % gradients.length];
}

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

function TeamLearningCard({ learning, index }: { learning: TeamLearning; index: number }) {
  const author = learning.author || 'Team Member';
  const initials = author
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
  const avatarGradient = stringToGradient(author);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.05, 0.3) }}
      className="group p-4 rounded-xl border border-[#fca311]/10 bg-[#14213d]/60 hover:bg-[#14213d]/80 hover:border-[#fca311]/20 transition-all"
    >
      <div className="flex gap-3">
        <div className={`h-10 w-10 rounded-xl bg-gradient-to-br ${avatarGradient} flex items-center justify-center shrink-0`}>
          <span className="text-black text-sm font-medium">{initials}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-white">{author}</span>
            <Badge
              variant="outline"
              className="bg-[#fca311]/10 text-[#fca311] border-[#fca311]/30 text-[10px] font-medium"
            >
              <Share2 className="w-2.5 h-2.5 mr-1" />
              Shared
            </Badge>
            <span className="text-xs text-[#e5e5e5]/50 flex items-center gap-1 ml-auto">
              <Clock className="w-3 h-3" />
              {formatTimeAgo(learning.timestamp)}
            </span>
          </div>
          <p className="text-sm text-[#e5e5e5]/80 line-clamp-3 leading-relaxed">{learning.insight}</p>
          {learning.tags && learning.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {learning.tags.slice(0, 4).map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="bg-[#fca311]/10 text-[#fca311] border border-[#fca311]/20 text-xs"
                >
                  #{tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

interface TeamFeedProps {
  className?: string;
  limit?: number;
}

export function TeamFeed({ className = '', limit = 10 }: TeamFeedProps) {
  const [learnings, setLearnings] = useState<TeamLearning[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTeamLearnings = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
        const response = await fetch(`${apiUrl}/learnings?limit=${limit}&team=true`);

        if (response.ok) {
          const data = await response.json();
          // Filter for shared learnings
          const shared = (data.learnings || []).filter(
            (l: TeamLearning) => l.shared
          );
          setLearnings(shared);
        }
      } catch (err) {
        console.error('Failed to fetch team learnings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTeamLearnings();
    const interval = setInterval(fetchTeamLearnings, 30000);
    return () => clearInterval(interval);
  }, [limit]);

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="h-24 rounded-xl shimmer"
            style={{ animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </div>
    );
  }

  if (learnings.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[#14213d] flex items-center justify-center">
          <Users className="w-8 h-8 text-[#fca311]/40" />
        </div>
        <p className="text-[#e5e5e5]/80 font-medium">No team learnings yet</p>
        <p className="text-[#e5e5e5]/40 text-sm mt-1">
          Share insights to see them here
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <AnimatePresence mode="popLayout">
        {learnings.map((learning, index) => (
          <TeamLearningCard
            key={learning.id}
            learning={learning}
            index={index}
          />
        ))}
      </AnimatePresence>
    </div>
  );
}

// Compact team activity widget for sidebar
export function TeamActivityWidget() {
  const [learnings, setLearnings] = useState<TeamLearning[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTeamLearnings = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';
        const response = await fetch(`${apiUrl}/learnings?limit=5&team=true`);

        if (response.ok) {
          const data = await response.json();
          const shared = (data.learnings || []).filter(
            (l: TeamLearning) => l.shared
          );
          setLearnings(shared.slice(0, 3));
        }
      } catch (err) {
        console.error('Failed to fetch team learnings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTeamLearnings();
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="rounded-2xl border border-[#fca311]/10 hover:border-[#fca311]/20 bg-[#14213d]/80 backdrop-blur-xl p-5 transition-colors duration-300"
    >
      <div className="flex items-center gap-2 mb-4">
        <Users className="w-5 h-5 text-[#fca311]" />
        <h3 className="font-semibold text-white">Team Activity</h3>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(2)].map((_, i) => (
            <div
              key={i}
              className="h-12 rounded-lg shimmer"
              style={{ animationDelay: `${i * 0.1}s` }}
            />
          ))}
        </div>
      ) : learnings.length === 0 ? (
        <div className="text-center py-4">
          <p className="text-[#e5e5e5]/60 text-sm">No team activity yet</p>
          <p className="text-[#e5e5e5]/40 text-xs mt-1">Share learnings to collaborate</p>
        </div>
      ) : (
        <div className="space-y-3">
          {learnings.map((learning, index) => {
            const author = learning.author || 'Team Member';
            const initials = author
              .split(' ')
              .map((n) => n[0])
              .join('')
              .toUpperCase()
              .slice(0, 2);
            const avatarGradient = stringToGradient(author);

            return (
              <motion.div
                key={learning.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-3 p-2 rounded-lg hover:bg-[#fca311]/5 transition-colors"
              >
                <div className={`h-7 w-7 rounded-lg bg-gradient-to-br ${avatarGradient} flex items-center justify-center shrink-0`}>
                  <span className="text-black text-[10px] font-medium">{initials}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-[#e5e5e5]/80 line-clamp-2 leading-relaxed">{learning.insight}</p>
                  <span className="text-[10px] text-[#e5e5e5]/40 mt-1 block">
                    {formatTimeAgo(learning.timestamp)}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
