"use client"

import * as React from "react"
import { Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface MessageBubbleProps {
  message: Message
  className?: string
}

function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

function highlightCitations(content: string): React.ReactNode {
  const parts = content.split(/(@\w+)/g)
  return parts.map((part, index) => {
    if (part.startsWith("@")) {
      return (
        <span
          key={index}
          className="font-medium text-primary bg-primary/10 px-1 rounded"
        >
          {part}
        </span>
      )
    }
    return part
  })
}

function renderMarkdown(content: string): React.ReactNode {
  // Simple markdown rendering for common patterns
  const lines = content.split("\n")
  const elements: React.ReactNode[] = []

  let inCodeBlock = false
  let codeBlockContent: string[] = []
  let codeBlockLang = ""

  lines.forEach((line, lineIndex) => {
    // Code block start/end
    if (line.startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`code-${lineIndex}`}
            className="bg-muted rounded-md p-3 overflow-x-auto text-sm my-2"
          >
            <code>{codeBlockContent.join("\n")}</code>
          </pre>
        )
        codeBlockContent = []
        inCodeBlock = false
      } else {
        inCodeBlock = true
        codeBlockLang = line.slice(3).trim()
      }
      return
    }

    if (inCodeBlock) {
      codeBlockContent.push(line)
      return
    }

    // Inline code
    if (line.includes("`")) {
      const parts = line.split(/(`[^`]+`)/g)
      const lineContent = parts.map((part, partIndex) => {
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code
              key={partIndex}
              className="bg-muted px-1.5 py-0.5 rounded text-sm"
            >
              {part.slice(1, -1)}
            </code>
          )
        }
        return highlightCitations(part)
      })
      elements.push(
        <p key={lineIndex} className="my-1">
          {lineContent}
        </p>
      )
      return
    }

    // Headers
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={lineIndex} className="font-semibold text-base mt-3 mb-1">
          {highlightCitations(line.slice(4))}
        </h3>
      )
      return
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={lineIndex} className="font-semibold text-lg mt-3 mb-1">
          {highlightCitations(line.slice(3))}
        </h2>
      )
      return
    }
    if (line.startsWith("# ")) {
      elements.push(
        <h1 key={lineIndex} className="font-bold text-xl mt-3 mb-1">
          {highlightCitations(line.slice(2))}
        </h1>
      )
      return
    }

    // Bold and italic
    let processedLine: React.ReactNode = line
    if (line.includes("**")) {
      const parts = line.split(/(\*\*[^*]+\*\*)/g)
      processedLine = parts.map((part, partIndex) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={partIndex}>{highlightCitations(part.slice(2, -2))}</strong>
          )
        }
        return highlightCitations(part)
      })
    } else {
      processedLine = highlightCitations(line)
    }

    // List items
    if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <li key={lineIndex} className="ml-4 list-disc">
          {typeof processedLine === "string"
            ? highlightCitations(line.slice(2))
            : processedLine}
        </li>
      )
      return
    }

    // Numbered lists
    const numberedMatch = line.match(/^(\d+)\.\s/)
    if (numberedMatch) {
      elements.push(
        <li key={lineIndex} className="ml-4 list-decimal">
          {highlightCitations(line.slice(numberedMatch[0].length))}
        </li>
      )
      return
    }

    // Empty lines
    if (line.trim() === "") {
      elements.push(<br key={lineIndex} />)
      return
    }

    // Regular paragraph
    elements.push(
      <p key={lineIndex} className="my-1">
        {processedLine}
      </p>
    )
  })

  return elements
}

export function MessageBubble({ message, className }: MessageBubbleProps) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "flex gap-3 w-full",
        isUser ? "flex-row-reverse" : "flex-row",
        className
      )}
    >
      <Avatar className="size-8 shrink-0">
        <AvatarFallback
          className={cn(
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground"
          )}
        >
          {isUser ? <User className="size-4" /> : <Bot className="size-4" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          "flex flex-col gap-1 max-w-[80%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-2 text-sm",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-muted text-foreground rounded-tl-sm"
          )}
        >
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {renderMarkdown(message.content)}
          </div>
        </div>

        <span className="text-xs text-muted-foreground px-1">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </div>
  )
}
