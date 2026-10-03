import "./Sidebar.css";
import type { FileRecord } from "../../views/ChatView";

interface Conversation {
  id: number;
  title: string;
}

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: number | null;
  onNewChat: () => void;
  onSelectConversation: (id: number) => void;
  files: FileRecord[];
  onDeleteFile: (fileId: number) => void;
  loading: boolean;
}

function Sidebar({
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
  files,
  onDeleteFile,
  loading,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-brand">
          <div className="brand-icon">✦</div>

          <div>
            <div className="brand-name">Local LLM</div>
            <div className="brand-subtitle">AI Assistant</div>
          </div>
        </div>

        <button
          type="button"
          className="new-chat-button"
          onClick={onNewChat}
        >
          <span className="new-chat-icon">+</span>
          <span>New Chat</span>
        </button>
      </div>

      <div className="conversation-section">
        <div className="conversation-label">Chats</div>

        <div className="conversation-list">
          {conversations.length === 0 ? (
            <div className="no-conversations">
              No conversations yet
            </div>
          ) : (
            conversations.map((conversation) => (
              <button
                type="button"
                key={conversation.id}
                className={`conversation-item ${
                  activeConversationId === conversation.id
                    ? "active"
                    : ""
                }`}
                onClick={() =>
                  onSelectConversation(conversation.id)
                }
              >
                <span className="conversation-icon">◦</span>

                <span className="conversation-title">
                  {conversation.title}
                </span>
              </button>
            ))
          )}
        </div>
      </div>

      {activeConversationId !== null && (
        <div className="sidebar-section files-section">
          <div className="sidebar-section-label">
            Files
            {files.length > 0 && (
              <span className="files-count">{files.length}</span>
            )}
          </div>

          <div className="file-list">
            {files.length === 0 ? (
              <div className="no-files">
                No files attached
              </div>
            ) : (
              files.map((file) => (
                <div
                  key={file.id}
                  className="file-item"
                  title={file.original_filename}
                >
                  <span className="file-item-icon">
                    {file.status === "parsed" ? "📄" : "⏳"}
                  </span>

                  <span className="file-item-name">
                    {file.original_filename}
                  </span>

                  <button
                    type="button"
                    className="file-item-delete"
                    onClick={() => onDeleteFile(file.id)}
                    disabled={loading}
                    aria-label={`Delete ${file.original_filename}`}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div className="sidebar-bottom" />
    </aside>
  );
}

export default Sidebar;