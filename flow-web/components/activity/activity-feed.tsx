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
  return (
    <div className="p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{session.summary}</p>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs">
              {session.branch}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {formatTimeAgo(session.timestamp)}
            </span>
          </div>
        </div>
      </div>

      {session.context?.blockers && session.context.blockers.length > 0 && (
        <div className="mt-2 pt-2 border-t">
          <p className="text-xs text-destructive font-medium">Blockers:</p>
          <ul className="text-xs text-muted-foreground mt-1">
            {session.context.blockers.map((blocker, i) => (
              <li key={i}>- {blocker}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function LearningCard({ learning }: { learning: Learning }) {
  const content = learning.insight || learning.text || "";

  return (
    <div className="p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
      <p className="text-sm">{content}</p>
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        {learning.tags.slice(0, 3).map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs">
            {tag}
          </Badge>
        ))}
        {learning.team && (
          <Badge variant="default" className="text-xs">
            team
          </Badge>
        )}
        <span className="text-xs text-muted-foreground ml-auto">
          {formatTimeAgo(learning.timestamp)}
        </span>
      </div>
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
