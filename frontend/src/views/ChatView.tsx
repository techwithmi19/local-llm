import { useState } from "react";
import "./ChatView.css";

interface Message {
  role: "user" | "assistant";
  content: string;
}

function ChatView() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    const message = input.trim();

    if (!message || loading) {
      return;
    }

    // Add user message immediately
    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: message,
      },
    ]);

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

      // Add LLM response
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.response,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            "Sorry, I couldn't process your request. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  return (
    <div className="chat-page">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-title">
          <h1>Personal Assistant</h1>
          <span>AI Assistant</span>
        </div>
      </header>

      {/* Messages */}
      <main className="chat-content">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <h2>How can I help?</h2>
            <p>
              Ask me anything. Your Local LLM assistant is ready.
            </p>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message-row ${message.role}`}
              >
                <div className="message">
                  {message.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message-row assistant">
                <div className="message typing">
                  Thinking...
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Input */}
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
    </div>
  );
}

export default ChatView;