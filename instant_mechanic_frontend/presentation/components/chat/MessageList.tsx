"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/domain/entities";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div
      className="flex flex-1 flex-col gap-1 overflow-y-auto py-4"
      role="log"
      aria-label="Conversation"
      aria-live="polite"
    >
      {messages.length === 0 && (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
          <div className="text-4xl" aria-hidden="true">🔧</div>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
            Instant Mechanic
          </h2>
          <p className="max-w-sm text-sm text-gray-500 dark:text-gray-400">
            Describe your vehicle issue and I&apos;ll help diagnose it. You can
            also upload photos, audio, or video.
          </p>
        </div>
      )}

      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && <TypingIndicator />}

      {/* Invisible scroll anchor */}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}
