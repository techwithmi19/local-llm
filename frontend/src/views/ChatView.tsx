import { useEffect, useMemo, useRef, useState } from "react";

import Sidebar from "../components/Sidebar/Sidebar";
import ChatHeader from "../components/Header/ChatHeader";
import MarkdownMessage from "../components/Chat/MarkdownMessage";
import FileAttachment from "../components/Chat/FileAttachment";

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

const EMPTY_RESPONSE_MESSAGE = "[No response received]";

export interface FileRecord {
  id: number;
  conversation_id: number;
  original_filename: string;
  mime_type: string;
  size: number;
  status: string;
}

function ChatView() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    number | null
  >(null);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [conversationFiles, setConversationFiles] = useState<
    FileRecord[]
  >([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isOverDropZone, setIsOverDropZone] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    selectedFilesRef.current = selectedFiles;
    console.log("selectedFiles updated:", selectedFiles.length, selectedFiles.map((f) => f.name));
  }, [selectedFiles]);

  const chatContentRef = useRef<HTMLElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const selectedFilesRef = useRef<File[]>([]);
  const skipLoadForConversationIdRef = useRef<number | null>(null);

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  const messages = useMemo(
    () => activeConversation?.messages ?? [],
    [activeConversation?.messages],
  );

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
   * Load messages and attached files whenever the active conversation changes.
   */
  useEffect(() => {
    if (activeConversationId === null) {
      return;
    }

    // Avoid overwriting state that is already being populated by an active
    // SSE stream right after a new conversation was created.
    if (skipLoadForConversationIdRef.current === activeConversationId) {
      skipLoadForConversationIdRef.current = null;
      return;
    }

    const loadConversation = async () => {
      try {
        const [conversationResponse, filesResponse] = await Promise.all([
          fetch(`/api/v1/conversations/${activeConversationId}`),
          fetch(`/api/v1/conversations/${activeConversationId}/files`),
        ]);

        if (!conversationResponse.ok) {
          throw new Error(
            `Failed to load conversation: ${conversationResponse.status}`,
          );
        }

        const data: Conversation = await conversationResponse.json();

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

        if (filesResponse.ok) {
          const filesData: FileRecord[] = await filesResponse.json();
          setConversationFiles(filesData);
        } else {
          setConversationFiles([]);
        }
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
   * Upload a list of files to a conversation.
   */
  const uploadFiles = async (
    conversationId: number,
    files: File[],
  ): Promise<FileRecord[]> => {
    const uploaded: FileRecord[] = [];

    for (const file of files) {
      console.log("uploadFiles uploading", file.name, file.type, file.size);
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `/api/v1/conversations/${conversationId}/files`,
        {
          method: "POST",
          body: formData,
        },
      );
      console.log("uploadFiles response", response.status, response.statusText);

      if (!response.ok) {
        const text = await response.text();
        throw new Error(
          `Failed to upload ${file.name}: ${response.status} ${text}`,
        );
      }

      const record: FileRecord = await response.json();
      console.log("uploadFiles record", record);
      uploaded.push(record);
    }

    return uploaded;
  };

  /*
   * Remove a file that is already attached to the conversation.
   */
  const removeConversationFile = async (fileId: number) => {
    try {
      const response = await fetch(`/api/v1/files/${fileId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`Failed to delete file: ${response.status}`);
      }

      setConversationFiles((previous) =>
        previous.filter((file) => file.id !== fileId),
      );
    } catch (error) {
      console.error("Failed to delete file:", error);
    }
  };

  /*
   * Send a message to the active conversation.
   */
  const sendMessage = async () => {
    const message = input.trim();
    const filesToUpload = selectedFilesRef.current;
    console.log("sendMessage called message=\"%s\" selectedFiles=%s ref=%s loading=%s", message, selectedFiles.length, filesToUpload.length, loading);

    if ((!message && filesToUpload.length === 0) || loading) {
      console.log("sendMessage early return");
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
                  : message || "File upload",
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
        skipLoadForConversationIdRef.current = conversationId;
      } catch (error) {
        console.error("Conversation creation error:", error);
        return;
      }
    }

    if (!conversationId) {
      return;
    }

    setInput("");
    setLoading(true);
    setUploadError(null);

    let uploaded: FileRecord[] = [];
    if (filesToUpload.length > 0) {
      setIsUploading(true);

      try {
        uploaded = await uploadFiles(
          conversationId,
          filesToUpload,
        );
        setConversationFiles((previous) => [
          ...previous,
          ...uploaded,
        ]);
        setSelectedFiles([]);
      } catch (error) {
        console.error("File upload error:", error);
        setUploadError(
          error instanceof Error
            ? error.message
            : "Failed to upload file(s)",
        );
      } finally {
        setIsUploading(false);
      }
    }

    if (!message) {
      setLoading(false);
      return;
    }

    // Collect IDs of files uploaded in this turn so the backend knows which
    // images to attach to the current message. This avoids resending every
    // image in the conversation on each turn.
    const uploadedFileIds = uploaded.map((file) => file.id);

    const assistantPlaceholderId = Date.now();

    try {
      const response = await fetch(
        `/api/v1/conversations/${conversationId}/messages/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            file_ids: uploadedFileIds,
          }),
        },
      );

      if (!response.ok || !response.body) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) {
            continue;
          }

          const data = line.slice(6).trim();
          if (!data || data === "[DONE]") {
            continue;
          }

          try {
            const event = JSON.parse(data) as {
              type: string;
              token?: string;
              user_message?: Message;
              assistant_message?: Message;
              error?: string;
            };

            if (
              event.type === "user_message" &&
              event.user_message
            ) {
              setConversations((previous) =>
                previous.map((conversation) =>
                  conversation.id === conversationId
                    ? {
                        ...conversation,
                        messages: [
                          ...conversation.messages,
                          event.user_message as Message,
                          {
                            id: assistantPlaceholderId,
                            conversation_id: conversationId,
                            role: "assistant",
                            content: "",
                            created_at: new Date().toISOString(),
                          },
                        ],
                      }
                    : conversation,
                ),
              );
            } else if (
              event.type === "token" &&
              typeof event.token === "string"
            ) {
              setConversations((previous) =>
                previous.map((conversation) =>
                  conversation.id === conversationId
                    ? {
                        ...conversation,
                        messages: conversation.messages.map(
                          (msg) =>
                            msg.id === assistantPlaceholderId
                              ? {
                                  ...msg,
                                  content: msg.content + event.token,
                                }
                              : msg,
                        ),
                      }
                    : conversation,
                ),
              );
            } else if (
              event.type === "done" &&
              event.assistant_message
            ) {
              const finalMessage: Message = {
                ...(event.assistant_message as Message),
                content:
                  (event.assistant_message as Message).content.trim() ||
                  EMPTY_RESPONSE_MESSAGE,
              };
              setConversations((previous) =>
                previous.map((conversation) =>
                  conversation.id === conversationId
                    ? {
                        ...conversation,
                        messages: conversation.messages.map(
                          (msg) =>
                            msg.id === assistantPlaceholderId
                              ? finalMessage
                              : msg,
                        ),
                      }
                    : conversation,
                ),
              );
            } else if (
              event.type === "error" &&
              typeof event.error === "string"
            ) {
              const errorMessage: Message = {
                id: Date.now(),
                conversation_id: conversationId,
                role: "assistant",
                content: event.error,
                created_at: new Date().toISOString(),
              };

              setConversations((previous) =>
                previous.map((conversation) =>
                  conversation.id === conversationId
                    ? {
                        ...conversation,
                        messages: conversation.messages.some(
                          (msg) => msg.id === assistantPlaceholderId,
                        )
                          ? conversation.messages.map((msg) =>
                              msg.id === assistantPlaceholderId
                                ? errorMessage
                                : msg,
                            )
                          : [...conversation.messages, errorMessage],
                      }
                    : conversation,
                ),
              );
            }
          } catch (parseError) {
            console.error("Failed to parse SSE event:", parseError);
          }
        }
      }
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
                messages: conversation.messages.some(
                  (msg) => msg.id === assistantPlaceholderId,
                )
                  ? conversation.messages.map((msg) =>
                      msg.id === assistantPlaceholderId
                        ? errorMessage
                        : msg,
                    )
                  : [...conversation.messages, errorMessage],
              }
            : conversation,
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const files = event.target.files;
    const filesArray = files ? Array.from(files) : [];
    console.log("handleFileSelect files:", files?.length, filesArray.map((f) => f.name));

    if (filesArray.length > 0) {
      setSelectedFiles((previous) => [...previous, ...filesArray]);
      setUploadError(null);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRemoveSelectedFile = (index: number) => {
    setSelectedFiles((previous) =>
      previous.filter((_, i) => i !== index),
    );
    setUploadError(null);
  };

  const handleDragOver = (
    event: React.DragEvent<HTMLElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    setIsOverDropZone(true);
  };

  const handleDragLeave = (
    event: React.DragEvent<HTMLElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    setIsOverDropZone(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsOverDropZone(false);

    const files = event.dataTransfer.files;
    const filesArray = files ? Array.from(files) : [];
    console.log("handleDrop files:", files?.length, filesArray.map((f) => f.name));

    if (filesArray.length > 0) {
      setSelectedFiles((previous) => [...previous, ...filesArray]);
      setUploadError(null);
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
    setSelectedFiles([]);
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
        files={conversationFiles}
        onDeleteFile={removeConversationFile}
        loading={loading}
      />

      <section className="chat-main">
        <ChatHeader
          conversationTitle={
            activeConversation?.title ?? "Local LLM"
          }
        />

        <main
          ref={chatContentRef}
          className={`chat-content ${
            isOverDropZone ? "drag-over" : ""
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isOverDropZone && (
            <div className="drop-overlay">
              Drop files here to attach them
            </div>
          )}

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
          {selectedFiles.length > 0 && (
            <div className="selected-files">
              {selectedFiles.map((file, index) => (
                <FileAttachment
                  key={`${file.name}-${index}`}
                  filename={file.name}
                  onRemove={() => handleRemoveSelectedFile(index)}
                  disabled={isUploading || loading}
                />
              ))}
            </div>
          )}

          {uploadError && (
            <div className="upload-error">{uploadError}</div>
          )}

          <div
            className={`chat-input-container ${
              isOverDropZone ? "drag-over" : ""
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <label
              className={`chat-input-attach ${
                isUploading || loading ? "disabled" : ""
              }`}
              aria-label="Attach file"
              title={
                isUploading || loading ? "Upload in progress" : "Attach file"
              }
            >
              📎
              <input
                ref={fileInputRef}
                type="file"
                multiple
                className="chat-file-input"
                tabIndex={-1}
                onChange={handleFileSelect}
                disabled={isUploading || loading}
              />
            </label>

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
              onClick={() => {
                console.log("send button clicked");
                void sendMessage();
              }}
              disabled={
                (!input.trim() && selectedFiles.length === 0) ||
                loading
              }
              aria-label="Send message"
            >
              {isUploading ? "⏳" : "↑"}
            </button>
          </div>

          <p className="input-hint">
            Enter to send · Shift + Enter for a new line · Drag & drop
            files to attach
          </p>
        </footer>
      </section>
    </div>
  );
}

export default ChatView;