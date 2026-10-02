import { useEffect, useState } from "react";

import "./ChatHeader.css";

interface ChatHeaderProps {
  conversationTitle: string;
}

interface AppConfig {
  provider: string;
  model: string;
}

function ChatHeader({
  conversationTitle,
}: ChatHeaderProps) {
  const [config, setConfig] = useState<AppConfig | null>(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await fetch("/api/v1/config");

        if (response.ok) {
          const data = (await response.json()) as AppConfig;
          setConfig(data);
        }
      } catch {
        // Ignore config fetch errors; fallback label will be shown.
      }
    };

    void loadConfig();
  }, []);

  const providerLabel = config?.provider
    ? config.provider.charAt(0).toUpperCase() + config.provider.slice(1)
    : null;

  const modelLabel = config?.model || null;

  const statusLabel =
    [providerLabel, modelLabel].filter(Boolean).join(" · ") ||
    "Local LLM";

  return (
    <header className="chat-header">
      <div className="chat-header-title">
        <h1>{conversationTitle || "Local LLM"}</h1>

        <div className="chat-header-model">
          <span className="status-dot" />
          <span>{statusLabel}</span>
        </div>
      </div>
    </header>
  );
}

export default ChatHeader;