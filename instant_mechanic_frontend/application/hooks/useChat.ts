"use client";

import { useCallback, useRef, useState } from "react";
import { chatApi } from "@/application/services/api";
import type { ChatMessage, DiagnosisResult } from "@/domain/entities";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [requiresBooking, setRequiresBooking] = useState(false);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Stable session ID for the lifetime of this component
  const sessionIdRef = useRef<string>(crypto.randomUUID());
  const sessionId = sessionIdRef.current;

  const appendMessage = useCallback(
    (role: "user" | "bot", content: string) => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role,
          content,
          timestamp: new Date().toISOString(),
        },
      ]);
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      // Optimistic: show user message immediately
      appendMessage("user", text);
      setIsLoading(true);
      setError(null);

      try {
        const response = await chatApi.sendMessage(sessionId, text);

        appendMessage("bot", response.message);
        setRequiresBooking(response.requires_booking);

        if (response.diagnosis) {
          setDiagnosis(response.diagnosis);
        }
      } catch {
        const msg =
          "Sorry, something went wrong connecting to the server. Please try again.";
        appendMessage("bot", msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading, appendMessage],
  );

  const resetChat = useCallback(() => {
    setMessages([]);
    setRequiresBooking(false);
    setDiagnosis(null);
    setError(null);
    sessionIdRef.current = crypto.randomUUID();
  }, []);

  return {
    messages,
    sendMessage,
    isLoading,
    requiresBooking,
    diagnosis,
    error,
    sessionId,
    resetChat,
    appendMessage,
  };
}
