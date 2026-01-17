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
        "p-3 rounded-lg border bg-card transition-all cursor-pointer",
        expanded ? "bg-accent/30 border-primary/30" : "hover:bg-accent/50"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className={cn(
            "text-sm font-medium leading-relaxed",
            !expanded && "line-clamp-2"
          )}>
            {session.summary}
          </p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <Badge variant="outline" className="text-xs shrink-0">
              {session.branch}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {formatTimeAgo(session.timestamp)}
            </span>
            <span className={cn(
              "text-xs ml-auto px-2 py-0.5 rounded-full shrink-0 transition-colors",
              expanded ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
            )}>
              {expanded ? "▲ Collapse" : "▼ Expand"}
            </span>
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t space-y-3">
          {/* Decisions */}
          {session.context?.decisions && session.context.decisions.length > 0 && (
            <div>
              <p className="text-xs font-medium text-green-400 mb-1">✓ Decisions Made</p>
              <ul className="text-sm space-y-1 pl-1">
                {session.context.decisions.map((decision, i) => (
                  <li key={i} className="text-muted-foreground">• {decision}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Next Steps */}
          {session.context?.next_steps && session.context.next_steps.length > 0 && (
            <div>
              <p className="text-xs font-medium text-blue-400 mb-1">→ Next Steps</p>
              <ul className="text-sm space-y-1 pl-1">
                {session.context.next_steps.map((step, i) => (
                  <li key={i} className="text-muted-foreground">• {step}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Blockers */}
          {session.context?.blockers && session.context.blockers.length > 0 && (
            <div>
              <p className="text-xs font-medium text-red-400 mb-1">⚠ Blockers</p>
              <ul className="text-sm space-y-1 pl-1">
                {session.context.blockers.map((blocker, i) => (
                  <li key={i} className="text-muted-foreground">• {blocker}</li>
                ))}
              </ul>
            </div>
          )}

          {/* No extra context message */}
          {(!session.context?.decisions?.length && !session.context?.next_steps?.length && !session.context?.blockers?.length) && (
            <p className="text-xs text-muted-foreground italic">No additional context captured for this session.</p>
          )}

          {/* Timestamp */}
          <div className="pt-2 border-t flex justify-between items-center">
            <p className="text-xs text-muted-foreground">
              {new Date(session.timestamp).toLocaleString()}
            </p>
            <span className="text-xs text-muted-foreground">ID: {session.id.slice(-8)}</span>
          </div>
        </div>
      )}

      {/* Collapsed Blockers Indicator */}
      {!expanded && session.context?.blockers && session.context.blockers.length > 0 && (
        <div className="mt-2 pt-2 border-t">
          <p className="text-xs text-destructive font-medium">
            {session.context.blockers.length} blocker{session.context.blockers.length > 1 ? "s" : ""}
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
        "p-3 rounded-lg border bg-card transition-all cursor-pointer",
        expanded ? "bg-accent/30" : "hover:bg-accent/50"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <p className={cn(
        "text-sm leading-relaxed",
        !expanded && "line-clamp-2"
      )}>
        {content}
      </p>
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        {learning.tags.slice(0, 3).map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs">
            {tag}
          </Badge>
        ))}
        {learning.team && (
          <Badge variant="default" className="text-xs bg-blue-500">
            team
          </Badge>
        )}
        <span className="text-xs text-muted-foreground ml-auto">
          {formatTimeAgo(learning.timestamp)}
        </span>
      </div>
      {expanded && learning.author && (
        <p className="text-xs text-muted-foreground mt-2 pt-2 border-t">
          By: {learning.author}
        </p>
      )}
    </div>
  );
}

export function ActivityFeed({ className }: ActivityFeedProps) {
  const { sessions, learnings, connected, lastUpdate } = useActivityStream();

  return (
    <div className={cn("flex flex-col h-full overflow-hidden", className)}>
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b">
        <h2 className="text-sm font-semibold">Activity</h2>
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              connected ? "bg-green-500" : "bg-red-500"
            )}
          />
          <span className="text-xs text-muted-foreground">
            {connected ? "Live" : "Disconnected"}
          </span>
        </div>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-4 space-y-6">
          {/* Recent Sessions */}
          {sessions.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
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
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
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
              <p className="text-sm text-muted-foreground">No recent activity</p>
              <p className="text-xs text-muted-foreground mt-1">
                Sessions and learnings will appear here
              </p>
            </div>
          )}

          {/* Last Update */}
          {lastUpdate && (
            <p className="text-xs text-center text-muted-foreground">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
