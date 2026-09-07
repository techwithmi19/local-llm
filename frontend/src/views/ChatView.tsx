import { useEffect, useRef, useState } from "react";

import Sidebar from "../components/Sidebar/Sidebar";
import ChatHeader from "../components/Header/ChatHeader";
import MarkdownMessage from "../components/Chat/MarkdownMessage";

import "./ChatView.css";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  id: number;
  title: string;
  messages: Message[];
}

function ChatView() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    number | null
  >(null);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatContentRef = useRef<HTMLElement>(null);

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  const messages = activeConversation?.messages ?? [];

  useEffect(() => {
    const chatContent = chatContentRef.current;

    if (!chatContent) {
      return;
    }

    chatContent.scrollTo({
      top: chatContent.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  const createConversation = () => {
    const id = Date.now();

    const conversation: Conversation = {
      id,
      title: "New Chat",
      messages: [],
    };

    setConversations((previous) => [...previous, conversation]);

    setActiveConversationId(id);
    setInput("");
  };

  const sendMessage = async () => {
    const message = input.trim();

    if (!message || loading) {
      return;
    }

    let conversationId = activeConversationId;

    if (!conversationId) {
      conversationId = Date.now();

      const newConversation: Conversation = {
        id: conversationId,
        title: message.length > 30 ? `${message.substring(0, 30)}...` : message,
        messages: [],
      };

      setConversations((previous) => [...previous, newConversation]);

      setActiveConversationId(conversationId);
    }

    const userMessage: Message = {
      role: "user",
      content: message,
    };

    setConversations((previous) =>
      previous.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              messages: [...conversation.messages, userMessage],
            }
          : conversation,
      ),
    );

    setInput("");
    setLoading(true);

    try {
      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
        }),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
      };

      setConversations((previous) =>
        previous.map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                messages: [...conversation.messages, assistantMessage],
              }
            : conversation,
        ),
      );
    } catch (error) {
      console.error("Chat error:", error);

      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, I couldn't process your request. Please try again.",
      };

      setConversations((previous) =>
        previous.map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                messages: [...conversation.messages, errorMessage],
              }
            : conversation,
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  const handleSelectConversation = (id: number) => {
    if (loading) {
      return;
    }

    setActiveConversationId(id);
    setInput("");
  };

  return (
    <div className="chat-app">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={createConversation}
        onSelectConversation={handleSelectConversation}
      />

      <section className="chat-main">
        <ChatHeader
          conversationTitle={activeConversation?.title ?? "Local LLM"}
        />

        <main ref={chatContentRef} className="chat-content">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div className="empty-icon">✦</div>

              <h2>How can I help?</h2>

              <p>Ask me anything. Your Local LLM assistant is ready.</p>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => (
                <div key={index} className={`message-row ${message.role}`}>
                  <div className="message">
                    <MarkdownMessage content={message.content} />
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row assistant">
                  <div className="message typing">Thinking...</div>
                </div>
              )}
            </div>
          )}
        </main>

        <footer className="chat-input-area">
          <div className="chat-input-container">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything..."
              rows={1}
              disabled={loading}
            />

            <button
              type="button"
              onClick={() => void sendMessage()}
              disabled={!input.trim() || loading}
              aria-label="Send message"
            >
              ↑
            </button>
          </div>

          <p className="input-hint">
            Enter to send · Shift + Enter for a new line
          </p>
        </footer>
      </section>
    </div>
  );
}

export default ChatView;
