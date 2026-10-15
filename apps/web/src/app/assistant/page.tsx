"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Plus, Trash2 } from "lucide-react";
import { chatApi, getAccessToken } from "@/lib/api";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/Skeleton";
import type { ChatSession, ChatMessage } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const SUGGESTED_PROMPTS = [
  "Who is most likely to score in tonight's match?",
  "Is there value in the top match this weekend?",
  "What are the chances of over 2.5 goals?",
  "Show me the Premier League standings",
  "What's the win probability for the next Lakers game?",
];

export default function AssistantPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatApi.getSessions().then((s) => {
      setSessions(s);
      if (s.length > 0) {
        loadSession(s[0]);
      }
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  const loadSession = async (session: ChatSession) => {
    setActiveSession(session);
    const msgs = await chatApi.getMessages(session.id);
    setMessages(msgs);
  };

  const createSession = async () => {
    const session = await chatApi.createSession();
    const newSession: ChatSession = {
      id: session.id,
      title: session.title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSession(newSession);
    setMessages([]);
  };

  const deleteSession = async (sessionId: string) => {
    await chatApi.deleteSession(sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSession?.id === sessionId) {
      setActiveSession(null);
      setMessages([]);
    }
  };

  const sendMessage = async (content: string) => {
    if (!content.trim() || streaming) return;

    let session = activeSession;
    if (!session) {
      const created = await chatApi.createSession();
      session = {
        id: created.id,
        title: created.title,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setSessions((prev) => [session!, ...prev]);
      setActiveSession(session);
    }

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      tool_calls: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);
    setStreamingText("");

    try {
      const token = getAccessToken();
      const response = await fetch(`${API_BASE}/chat/sessions/${session.id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Failed to send message");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "text") {
                fullText += data.content;
                setStreamingText(fullText);
              } else if (data.type === "done") {
                const assistantMsg: ChatMessage = {
                  id: crypto.randomUUID(),
                  role: "assistant",
                  content: fullText,
                  tool_calls: [],
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, assistantMsg]);
                setStreamingText("");
              }
            } catch {
              // ignore parse errors
            }
          }
        }
      }
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        tool_calls: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setStreaming(false);
      setStreamingText("");
    }
  };

  return (
    <AppShell>
      <div className="flex h-[calc(100vh-8rem)] gap-4">
        {/* Session sidebar */}
        <div className="hidden md:flex flex-col w-56 flex-shrink-0">
          <button onClick={createSession} className="btn-primary flex items-center gap-2 mb-3">
            <Plus className="w-4 h-4" aria-hidden />
            New chat
          </button>
          <div className="flex-1 overflow-y-auto space-y-1">
            {loading ? (
              <Skeleton className="h-8 w-full" />
            ) : (
              sessions.map((s) => (
                <div
                  key={s.id}
                  className={`group flex items-center gap-2 px-3 py-2 rounded-button cursor-pointer text-body-sm transition-colors ${
                    activeSession?.id === s.id
                      ? "bg-accent-tint text-accent"
                      : "text-text-secondary hover:bg-surface"
                  }`}
                  onClick={() => loadSession(s)}
                >
                  <span className="flex-1 truncate">{s.title}</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                    className="opacity-0 group-hover:opacity-100 text-text-secondary hover:text-live"
                    aria-label="Delete chat"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col card p-0 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && !streaming && (
              <div className="flex flex-col items-center justify-center h-full gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-accent-tint rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-accent text-section-title">B</span>
                  </div>
                  <h2 className="text-section-title font-heading text-text-primary mb-1">
                    BetLens Assistant
                  </h2>
                  <p className="text-body-sm text-text-secondary max-w-sm">
                    Ask me about match probabilities, team form, player stats, or odds value.
                    Every number I give comes from real platform data.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => sendMessage(prompt)}
                      className="text-left text-body-sm text-text-secondary bg-surface hover:bg-accent-tint hover:text-accent rounded-button px-3 py-2 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-card px-4 py-3 text-body-sm ${
                    msg.role === "user"
                      ? "bg-accent text-white"
                      : "bg-surface text-text-primary"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}

            {/* Streaming response */}
            {streaming && streamingText && (
              <div className="flex justify-start">
                <div className="max-w-[80%] bg-surface rounded-card px-4 py-3 text-body-sm text-text-primary">
                  <p className="whitespace-pre-wrap">{streamingText}</p>
                  <span className="inline-block w-1 h-4 bg-accent animate-pulse ml-0.5" />
                </div>
              </div>
            )}

            {streaming && !streamingText && (
              <div className="flex justify-start">
                <div className="bg-surface rounded-card px-4 py-3">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="w-2 h-2 bg-text-secondary rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Disclaimer */}
          <div className="px-4 py-1 border-t border-border">
            <p className="disclaimer text-center">
              Estimates based on statistical models. No outcome is guaranteed. 18+ only.
            </p>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-border">
            <form
              onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about tonight's matches…"
                className="input flex-1"
                disabled={streaming}
              />
              <button
                type="submit"
                disabled={!input.trim() || streaming}
                className="btn-primary flex items-center gap-2"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" aria-hidden />
              </button>
            </form>
          </div>
        </div>
      </div>
    </AppShell>
  );
}