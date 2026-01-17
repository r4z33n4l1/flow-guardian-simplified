"use client"

import * as React from "react"
import { Send, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function ChatInput({
  onSend,
  isLoading = false,
  placeholder = "Type a message...",
  className,
  disabled = false,
}: ChatInputProps) {
  const [value, setValue] = React.useState("")
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  const handleSubmit = React.useCallback(() => {
    const trimmedValue = value.trim()
    if (trimmedValue && !isLoading && !disabled) {
      onSend(trimmedValue)
      setValue("")
      // Reset textarea height after sending
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
    }
  }, [value, isLoading, disabled, onSend])

  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  const handleChange = React.useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setValue(e.target.value)
      // Auto-resize textarea
      const textarea = e.target
      textarea.style.height = "auto"
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    },
    []
  )

  return (
    <div className={cn("flex items-end gap-2", className)}>
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading || disabled}
        className={cn(
          "min-h-[44px] max-h-[200px] resize-none py-3",
          "focus-visible:ring-1"
        )}
        rows={1}
      />
      <Button
        size="icon"
        onClick={handleSubmit}
        disabled={!value.trim() || isLoading || disabled}
        className="shrink-0 size-11"
      >
        {isLoading ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Send className="size-4" />
        )}
        <span className="sr-only">Send message</span>
      </Button>
    </div>
  )
}
