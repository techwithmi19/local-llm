import "./Sidebar.css";

interface Conversation {
  id: number;
  title: string;
}

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: number | null;
  onNewChat: () => void;
  onSelectConversation: (id: number) => void;
}

function Sidebar({
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
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

      <div className="sidebar-bottom" />
    </aside>
  );
}

export default Sidebar;