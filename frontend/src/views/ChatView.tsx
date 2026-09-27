import { useEffect, useRef, useState } from "react";

import Sidebar from "../components/Sidebar/Sidebar";
import ChatHeader from "../components/Header/ChatHeader";
import MarkdownMessage from "../components/Chat/MarkdownMessage";

import "./ChatView.css";

interface Message {
  id: number;
  conversation_id: number | null;
  role: "user" | "assistant";
  content: string;
  created_at: string;
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
  const [initialLoading, setInitialLoading] = useState(true);

  const chatContentRef = useRef<HTMLElement>(null);

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  const messages = activeConversation?.messages ?? [];

  /*
   * Load conversations when the page is opened/refreshed.
   */
  useEffect(() => {
    const loadConversations = async () => {
      try {
        const response = await fetch("/api/v1/conversations");

        if (!response.ok) {
          throw new Error(
            `Failed to load conversations: ${response.status}`,
          );
        }

        const data: Array<{
          id: number;
          title: string;
        }> = await response.json();

        const loadedConversations: Conversation[] = data.map(
          (conversation) => ({
            id: conversation.id,
            title: conversation.title,
            messages: [],
          }),
        );

        setConversations(loadedConversations);

        /*
         * Restore the first conversation when the page is refreshed.
         */
        if (loadedConversations.length > 0) {
          setActiveConversationId(loadedConversations[0].id);
        }
      } catch (error) {
        console.error("Failed to load conversations:", error);
      } finally {
        setInitialLoading(false);
      }
    };

    void loadConversations();
  }, []);

  /*
   * Load messages whenever the active conversation changes.
   */
  useEffect(() => {
    if (activeConversationId === null) {
      return;
    }

    const loadConversation = async () => {
      try {
        const response = await fetch(
          `/api/v1/conversations/${activeConversationId}`,
        );

        if (!response.ok) {
          throw new Error(
            `Failed to load conversation: ${response.status}`,
          );
        }

        const data: Conversation = await response.json();

        setConversations((previous) =>
          previous.map((conversation) =>
            conversation.id === data.id
              ? {
                  ...conversation,
                  title: data.title,
                  messages: data.messages,
                }
              : conversation,
          ),
        );
      } catch (error) {
        console.error("Failed to load conversation:", error);
      }
    };

    void loadConversation();
  }, [activeConversationId]);

  /*
   * Scroll to the bottom whenever messages or loading state changes.
   */
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

  /*
   * Create a new conversation in the database.
   */
  const createConversation = async () => {
    if (loading) {
      return;
    }

    try {
      const response = await fetch("/api/v1/conversations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "New Chat",
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Failed to create conversation: ${response.status}`,
        );
      }

      const data: {
        id: number;
        title: string;
      } = await response.json();

      const newConversation: Conversation = {
        id: data.id,
        title: data.title,
        messages: [],
      };

      setConversations((previous) => [
        ...previous,
        newConversation,
      ]);

      setActiveConversationId(data.id);
      setInput("");
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  /*
   * Send a message to the active conversation.
   */
  const sendMessage = async () => {
    const message = input.trim();

    if (!message || loading) {
      return;
    }

    let conversationId = activeConversationId;

    if (!conversationId) {
      try {
        const conversationResponse = await fetch(
          "/api/v1/conversations",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              title:
                message.length > 30
                  ? `${message.substring(0, 30)}...`
                  : message,
            }),
          },
        );

        if (!conversationResponse.ok) {
          throw new Error(
            `Conversation creation failed: ${conversationResponse.status}`,
          );
        }

        const conversationData = await conversationResponse.json();

        conversationId = conversationData.id;

        setConversations((previous) => [
          ...previous,
          {
            id: conversationData.id,
            title: conversationData.title,
            messages: [],
          },
        ]);

        setActiveConversationId(conversationId);
      } catch (error) {
        console.error("Conversation creation error:", error);
        return;
      }
    }

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        `/api/v1/conversations/${conversationId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();

      setConversations((previous) =>
        previous.map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                messages: [
                  ...conversation.messages,
                  data.user_message,
                  data.assistant_message,
                ],
              }
            : conversation,
        ),
      );
    } catch (error) {
      console.error("Chat error:", error);

      const errorMessage: Message = {
        id: Date.now(),
        conversation_id: conversationId,
        role: "assistant",
        content:
          "Sorry, I couldn't process your request. Please try again.",
        created_at: new Date().toISOString(),
      };

      setConversations((previous) =>
        previous.map((conversation) =>
          conversation.id === conversationId
            ? {
                ...conversation,
                messages: [
                  ...conversation.messages,
                  errorMessage,
                ],
              }
            : conversation,
        ),
      );
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

  const handleSelectConversation = (id: number) => {
    if (loading) {
      return;
    }

    setActiveConversationId(id);
    setInput("");
  };

  if (initialLoading) {
    return (
      <div className="chat-app">
        <div className="chat-main">
          <main className="chat-content">
            <div className="chat-empty">
              <div className="empty-icon">✦</div>

              <h2>Loading conversations...</h2>

              <p>Please wait while your chat history is loaded.</p>
            </div>
          </main>
        </div>
      </div>
    );
  }

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
          conversationTitle={
            activeConversation?.title ?? "Local LLM"
          }
        />

        <main ref={chatContentRef} className="chat-content">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div className="empty-icon">✦</div>

              <h2>How can I help?</h2>

              <p>
                Ask me anything. Your Local LLM assistant is ready.
              </p>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message-row ${message.role}`}
                >
                  <div className="message">
                    <MarkdownMessage
                      content={message.content}
                    />
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