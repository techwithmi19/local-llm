import "./ChatHeader.css";

interface ChatHeaderProps {
  conversationTitle: string;
}

function ChatHeader({
  conversationTitle,
}: ChatHeaderProps) {
  return (
    <header className="chat-header">
      <div className="chat-header-title">
        <h1>{conversationTitle || "Local LLM"}</h1>

        <div className="chat-header-model">
          <span className="status-dot" />
          <span>Groq · Compound</span>
        </div>
      </div>
    </header>
  );
}

export default ChatHeader;