"use client"

import { cn } from "@/lib/utils"

interface TypingIndicatorProps {
  className?: string
  message?: string
}

export function TypingIndicator({ className, message }: TypingIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="sr-only">Assistant is typing</span>
      <div className="flex items-center gap-1">
        <span
          className="size-2 rounded-full bg-primary/60 animate-bounce"
          style={{ animationDelay: "0ms", animationDuration: "600ms" }}
        />
        <span
          className="size-2 rounded-full bg-primary/60 animate-bounce"
          style={{ animationDelay: "150ms", animationDuration: "600ms" }}
        />
        <span
          className="size-2 rounded-full bg-primary/60 animate-bounce"
          style={{ animationDelay: "300ms", animationDuration: "600ms" }}
        />
      </div>
      {message && (
        <span className="text-xs text-muted-foreground animate-pulse">
          {message}
        </span>
      )}
    </div>
  )
}

interface LoadingStateProps {
  stage: "searching" | "thinking" | "generating"
  className?: string
}

export function LoadingState({ stage, className }: LoadingStateProps) {
  const messages = {
    searching: "Searching team memories...",
    thinking: "Analyzing context...",
    generating: "Generating response...",
  }

  const icons = {
    searching: "🔍",
    thinking: "🧠",
    generating: "✨",
  }

  return (
    <div className={cn("flex items-center gap-3 p-4 rounded-lg bg-muted/50", className)}>
      <span className="text-lg animate-pulse">{icons[stage]}</span>
      <div className="flex-1">
        <p className="text-sm font-medium">{messages[stage]}</p>
        <div className="flex items-center gap-1 mt-1">
          <span
            className="size-1.5 rounded-full bg-primary animate-bounce"
            style={{ animationDelay: "0ms", animationDuration: "600ms" }}
          />
          <span
            className="size-1.5 rounded-full bg-primary animate-bounce"
            style={{ animationDelay: "150ms", animationDuration: "600ms" }}
          />
          <span
            className="size-1.5 rounded-full bg-primary animate-bounce"
            style={{ animationDelay: "300ms", animationDuration: "600ms" }}
          />
        </div>
      </div>
    </div>
  )
}
