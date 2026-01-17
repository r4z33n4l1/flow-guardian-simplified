"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useActivityStream,
  type Session,
  type Learning,
} from "@/lib/hooks/use-activity-stream";

interface ActivityFeedProps {
  className?: string;
}

function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const then = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function SessionCard({ session }: { session: Session }) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div
      className={cn(
        "p-3 rounded-xl border border-[#E8E0D4] bg-white transition-all cursor-pointer",
        expanded ? "bg-orange-50/50 border-orange-200" : "hover:bg-[#F5F0E8]"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className={cn(
            "text-sm font-medium leading-relaxed text-[#2D2A26]",
            !expanded && "line-clamp-2"
          )}>
            {session.summary}
          </p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <Badge variant="outline" className="text-xs shrink-0 bg-[#F5F0E8] text-[#6B6560] border-[#E8E0D4]">
              {session.branch}
            </Badge>
            <span className="text-xs text-[#6B6560]">
              {formatTimeAgo(session.timestamp)}
            </span>
            <span className={cn(
              "text-xs ml-auto px-2 py-0.5 rounded-full shrink-0 transition-colors",
              expanded ? "bg-orange-100 text-orange-600" : "bg-[#F5F0E8] text-[#6B6560]"
            )}>
              {expanded ? "▲ Collapse" : "▼ Expand"}
            </span>
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-[#E8E0D4] space-y-3">
          {/* Hypothesis */}
          {session.context?.hypothesis && (
            <div>
              <p className="text-xs font-medium text-purple-600 mb-1">💡 Hypothesis</p>
              <p className="text-sm text-[#6B6560] pl-1">{session.context.hypothesis}</p>
            </div>
          )}

          {/* Decisions - at root level */}
          {session.decisions && session.decisions.length > 0 && (
            <div>
              <p className="text-xs font-medium text-green-600 mb-1">✓ Decisions Made</p>
              <ul className="text-sm space-y-1 pl-1">
                {session.decisions.map((decision, i) => (
                  <li key={i} className="text-[#6B6560]">• {decision}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Next Steps - in context */}
          {session.context?.next_steps && session.context.next_steps.length > 0 && (
            <div>
              <p className="text-xs font-medium text-orange-600 mb-1">→ Next Steps</p>
              <ul className="text-sm space-y-1 pl-1">
                {session.context.next_steps.map((step, i) => (
                  <li key={i} className="text-[#6B6560]">• {step}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Files */}
          {session.context?.files && session.context.files.length > 0 && (
            <div>
              <p className="text-xs font-medium text-blue-600 mb-1">📁 Files ({session.context.files.length})</p>
              <ul className="text-sm space-y-1 pl-1">
                {session.context.files.slice(0, 5).map((file, i) => (
                  <li key={i} className="text-[#6B6560] font-mono text-xs truncate">• {file}</li>
                ))}
                {session.context.files.length > 5 && (
                  <li className="text-[#9a918a] text-xs">...and {session.context.files.length - 5} more</li>
                )}
              </ul>
            </div>
          )}

          {/* Blockers - check both root and context */}
          {((session.blockers && session.blockers.length > 0) || (session.context?.blockers && session.context.blockers.length > 0)) && (
            <div>
              <p className="text-xs font-medium text-red-600 mb-1">⚠ Blockers</p>
              <ul className="text-sm space-y-1 pl-1">
                {(session.blockers || session.context?.blockers || []).map((blocker, i) => (
                  <li key={i} className="text-[#6B6560]">• {blocker}</li>
                ))}
              </ul>
            </div>
          )}

          {/* No extra context message */}
          {(!session.decisions?.length && !session.context?.next_steps?.length && !session.context?.files?.length && !session.blockers?.length && !session.context?.blockers?.length && !session.context?.hypothesis) && (
            <p className="text-xs text-[#9a918a] italic">No additional context captured for this session.</p>
          )}

          {/* Timestamp */}
          <div className="pt-2 border-t border-[#E8E0D4] flex justify-between items-center">
            <p className="text-xs text-[#9a918a]">
              {new Date(session.timestamp).toLocaleString()}
            </p>
            <span className="text-xs text-[#9a918a]">ID: {session.id.slice(-8)}</span>
          </div>
        </div>
      )}

      {/* Collapsed Blockers Indicator */}
      {!expanded && ((session.blockers && session.blockers.length > 0) || (session.context?.blockers && session.context.blockers.length > 0)) && (
        <div className="mt-2 pt-2 border-t border-[#E8E0D4]">
          <p className="text-xs text-red-600 font-medium">
            {(session.blockers || session.context?.blockers || []).length} blocker{(session.blockers || session.context?.blockers || []).length > 1 ? "s" : ""}
          </p>
        </div>
      )}
    </div>
  );
}

function LearningCard({ learning }: { learning: Learning }) {
  const [expanded, setExpanded] = React.useState(false);
  const content = learning.insight || learning.text || "";

  return (
    <div
      className={cn(
        "p-3 rounded-xl border border-[#E8E0D4] bg-white transition-all cursor-pointer",
        expanded ? "bg-orange-50/50 border-orange-200" : "hover:bg-[#F5F0E8]"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <p className={cn(
        "text-sm leading-relaxed text-[#2D2A26]",
        !expanded && "line-clamp-2"
      )}>
        {content}
      </p>
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        {learning.tags.slice(0, 3).map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs bg-[#F5F0E8] text-[#6B6560] border border-[#E8E0D4]">
            {tag}
          </Badge>
        ))}
        {learning.team && (
          <Badge variant="default" className="text-xs bg-orange-500 text-white border-orange-500">
            team
          </Badge>
        )}
        <span className="text-xs text-[#6B6560] ml-auto">
          {formatTimeAgo(learning.timestamp)}
        </span>
      </div>
      {expanded && learning.author && (
        <p className="text-xs text-[#9a918a] mt-2 pt-2 border-t border-[#E8E0D4]">
          By: {learning.author}
        </p>
      )}
    </div>
  );
}

export function ActivityFeed({ className }: ActivityFeedProps) {
  const { sessions, learnings, connected, lastUpdate } = useActivityStream();

  return (
    <div className={cn("flex flex-col h-full overflow-hidden bg-[#FAF8F5]", className)}>
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-[#E8E0D4]">
        <h2 className="text-sm font-semibold text-[#2D2A26]">Activity</h2>
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              connected ? "bg-green-500" : "bg-red-500"
            )}
          />
          <span className="text-xs text-[#6B6560]">
            {connected ? "Live" : "Disconnected"}
          </span>
        </div>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-4 space-y-6">
          {/* Recent Sessions */}
          {sessions.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-[#6B6560] uppercase tracking-wider mb-3">
                Recent Sessions
              </h3>
              <div className="space-y-2">
                {sessions.slice(0, 5).map((session) => (
                  <SessionCard key={session.id} session={session} />
                ))}
              </div>
            </div>
          )}

          {/* Recent Learnings */}
          {learnings.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-[#6B6560] uppercase tracking-wider mb-3">
                Recent Learnings
              </h3>
              <div className="space-y-2">
                {learnings.slice(0, 5).map((learning, index) => (
                  <LearningCard key={`${learning.id}-${index}`} learning={learning} />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {sessions.length === 0 && learnings.length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <p className="text-sm text-[#6B6560]">No recent activity</p>
              <p className="text-xs text-[#9a918a] mt-1">
                Sessions and learnings will appear here
              </p>
            </div>
          )}

          {/* Last Update */}
          {lastUpdate && (
            <p className="text-xs text-center text-[#9a918a]">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
