"use client"

import * as React from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageBubble, type Message } from "./message-bubble"
import { ChatInput } from "./chat-input"
import { TypingIndicator, LoadingState } from "./typing-indicator"

type ConnectionStatus = "connected" | "disconnected" | "connecting"

interface ChatInterfaceProps {
  /** Function to fetch messages */
  fetchMessages?: () => Promise<Message[]>
  /** Function to send a message */
  sendMessage?: (content: string) => Promise<Message>
  /** Query key for React Query */
  queryKey?: string[]
  /** Initial messages if not using fetch */
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
  fetchMessages,
  sendMessage,
  queryKey = ["chat", "messages"],
  initialMessages = [],
  connectionStatus = "connected",
  title = "Chat",
  showHeader = true,
  className,
  height = "h-[600px]",
}: ChatInterfaceProps) {
  const queryClient = useQueryClient()
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)
  const [isStreaming, setIsStreaming] = React.useState(false)

  // Fetch messages using React Query
  const {
    data: messages = initialMessages,
    isLoading: isLoadingMessages,
  } = useQuery({
    queryKey,
    queryFn: fetchMessages ?? (() => Promise.resolve(initialMessages)),
    enabled: !!fetchMessages,
    initialData: initialMessages,
  })

  // Send message mutation
  const sendMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!sendMessage) {
        // Create a local message if no sendMessage function provided
        const userMessage: Message = {
          id: crypto.randomUUID(),
          role: "user",
          content,
          timestamp: new Date(),
        }
        return userMessage
      }
      return sendMessage(content)
    },
    onMutate: async (content) => {
      // Optimistic update: add user message immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: new Date(),
      }

      await queryClient.cancelQueries({ queryKey })
      const previousMessages = queryClient.getQueryData<Message[]>(queryKey)

      queryClient.setQueryData<Message[]>(queryKey, (old = []) => [
        ...old,
        userMessage,
      ])

      setIsStreaming(true)

      return { previousMessages, userMessage }
    },
    onSuccess: (response, _, context) => {
      // If sendMessage returned an assistant response, add it
      if (response && response.role === "assistant") {
        queryClient.setQueryData<Message[]>(queryKey, (old = []) => [
          ...old,
          response,
        ])
      }
      setIsStreaming(false)
    },
    onError: (_, __, context) => {
      // Rollback on error
      if (context?.previousMessages) {
        queryClient.setQueryData(queryKey, context.previousMessages)
      }
      setIsStreaming(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey })
    },
  })

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

  const handleSend = React.useCallback(
    (content: string) => {
      sendMutation.mutate(content)
    },
    [sendMutation]
  )

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
            {isLoadingMessages ? (
              <div className="flex items-center justify-center py-8">
                <TypingIndicator />
              </div>
            ) : messages.length === 0 ? (
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
            onSend={handleSend}
            isLoading={sendMutation.isPending}
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
