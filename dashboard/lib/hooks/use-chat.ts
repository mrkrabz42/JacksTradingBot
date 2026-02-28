"use client";

import { useState, useCallback } from "react";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

const GREETING: ChatMessage = {
  id: "greeting",
  role: "assistant",
  content:
    "Hey there! I'm Mr 10Krabs. Ask me about MSS events, displacement rules, session levels, or your progress to $10K.",
  timestamp: Date.now(),
};

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: content.trim(),
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setError(null);

      try {
        // Build conversation for API (exclude greeting, only role+content)
        const apiMessages = [...messages.filter((m) => m.id !== "greeting"), userMsg].map(
          (m) => ({ role: m.role, content: m.content })
        );

        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: apiMessages }),
        });

        if (!res.ok) {
          throw new Error(`Request failed (${res.status})`);
        }

        const data = await res.json();

        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply ?? "Sorry, I didn't get a response.",
          timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Something went wrong";
        setError(msg);

        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "Snap! Something went wrong. Try again in a moment.",
          timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, isLoading]
  );

  const clearChat = useCallback(() => {
    setMessages([{ ...GREETING, timestamp: Date.now() }]);
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, clearChat };
}
