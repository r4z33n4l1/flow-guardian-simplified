"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageBubble, type Message } from "./message-bubble"
import { ChatInput } from "./chat-input"
import { LoadingState } from "./typing-indicator"

type ConnectionStatus = "connected" | "disconnected" | "connecting"

interface ChatInterfaceProps {
  /** Function to send a message */
  sendMessage?: (content: string) => Promise<Message>
  /** Initial messages */
  initialMessages?: Message[]
  /** Connection status */
  connectionStatus?: ConnectionStatus
  /** Title for the chat header */
  title?: string
  /** Show header */
  showHeader?: boolean
  /** Custom class name */
  className?: string
  /** Height of the chat container */
  height?: string
}

const statusConfig: Record<
  ConnectionStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  connected: { label: "Connected", variant: "default" },
  connecting: { label: "Connecting...", variant: "secondary" },
  disconnected: { label: "Disconnected", variant: "destructive" },
}

export function ChatInterface({
  sendMessage,
  initialMessages = [],
  connectionStatus = "connected",
  title = "Chat",
  showHeader = true,
  className,
  height = "h-[600px]",
}: ChatInterfaceProps) {
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)
  const [isStreaming, setIsStreaming] = React.useState(false)
  const [isSending, setIsSending] = React.useState(false)

  // Local state for messages - simple and reliable
  const [messages, setMessages] = React.useState<Message[]>(initialMessages)

  // Handle sending messages
  const handleSendMessage = React.useCallback(async (content: string) => {
    // Create user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
    }

    // Add user message immediately
    setMessages(prev => [...prev, userMessage])
    setIsStreaming(true)
    setIsSending(true)

    try {
      if (sendMessage) {
        const response = await sendMessage(content)

        // Add assistant response
        if (response && response.role === "assistant") {
          setMessages(prev => [...prev, response])
        }
      }
    } catch (error) {
      console.error("Failed to send message:", error)
    } finally {
      setIsStreaming(false)
      setIsSending(false)
    }
  }, [sendMessage])

  // Auto-scroll to bottom when messages change
  React.useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-slot='scroll-area-viewport']"
      )
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages, isStreaming])

  const status = statusConfig[connectionStatus]

  return (
    <Card className={cn("flex flex-col", height, className)}>
      {showHeader && (
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-4 border-b">
          <CardTitle className="text-lg">{title}</CardTitle>
          <Badge variant={status.variant}>{status.label}</Badge>
        </CardHeader>
      )}

      <CardContent className="flex-1 flex flex-col p-0 min-h-0">
        <ScrollArea ref={scrollAreaRef} className="flex-1 min-h-0">
          <div className="flex flex-col gap-4 p-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
                No messages yet. Start a conversation!
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}

            {isStreaming && (
              <LoadingState stage="searching" className="max-w-md" />
            )}
          </div>
        </ScrollArea>

        <div className="p-4 border-t">
          <ChatInput
            onSend={handleSendMessage}
            isLoading={isSending}
            disabled={connectionStatus === "disconnected"}
            placeholder={
              connectionStatus === "disconnected"
                ? "Connection lost..."
                : "Type a message..."
            }
          />
        </div>
      </CardContent>
    </Card>
  )
}
