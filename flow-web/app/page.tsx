"use client";

import { useState } from "react";
import Link from "next/link";
import { ChatInterface } from "@/components/chat/chat-interface";
import type { Message } from "@/components/chat/message-bubble";
import { UploadModal } from "@/components/upload/upload-modal";
import { ActivityFeed } from "@/components/activity/activity-feed";
import { SuggestionsWidget } from "@/components/suggestions/suggestions-panel";
import { Button } from "@/components/ui/button";
import { Network, LayoutDashboard, Upload, Activity } from "lucide-react";

export default function Home() {
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [showActivity, setShowActivity] = useState(true);
  const sendMessage = async (content: string): Promise<Message> => {
    // Send to chat API
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content }],
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to send message");
    }

    // Handle streaming response
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullContent = "";

    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") continue;

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                fullContent += parsed.content;
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    }

    return {
      id: crypto.randomUUID(),
      role: "assistant",
      content: fullContent || "I couldn't find relevant context to answer your question.",
      timestamp: new Date(),
    };
  };

  return (
    <div className="h-screen flex flex-col bg-[#FAF8F5] overflow-hidden">
      <header className="flex-shrink-0 border-b border-[#E8E0D4] px-6 py-3 bg-[#FAF8F5]/80 backdrop-blur">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-orange-500">
                <Network className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-[#2D2A26]">Flow Guardian</h1>
                <p className="text-xs text-[#6B6560]">AI Team Memory</p>
              </div>
            </div>
            <nav className="hidden md:flex items-center gap-1">
              <Link href="/graph">
                <Button variant="ghost" size="sm" className="gap-2 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50">
                  <Network className="w-4 h-4" />
                  Graph
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="gap-2 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50">
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </Button>
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowActivity(!showActivity)}
              className="gap-2 text-[#6B6560] hover:text-orange-500 hover:bg-orange-50"
            >
              <Activity className="w-4 h-4" />
              <span className="hidden sm:inline">{showActivity ? "Hide" : "Show"}</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsUploadOpen(true)}
              className="gap-2 border-[#E8E0D4] text-[#6B6560] hover:bg-orange-50 hover:text-orange-500 hover:border-orange-300"
            >
              <Upload className="w-4 h-4" />
              <span className="hidden sm:inline">Add Context</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col min-h-0 p-4">
          <div className="flex-1 min-h-0 max-w-4xl w-full mx-auto">
            <ChatInterface
              title="Ask about your team's work"
              sendMessage={sendMessage}
              height="h-full"
              showHeader={false}
            />
          </div>
        </main>

        {/* Activity Sidebar */}
        {showActivity && (
          <aside className="w-96 flex-shrink-0 border-l border-[#E8E0D4] bg-[#F5F0E8]/50 hidden lg:block overflow-hidden">
            <ActivityFeed className="h-full" />
          </aside>
        )}
      </div>

      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadComplete={() => setIsUploadOpen(false)}
      />

      {/* AI Suggestions Widget */}
      <SuggestionsWidget />
    </div>
  );
}
