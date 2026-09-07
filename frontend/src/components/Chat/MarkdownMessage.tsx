import { useState, type ReactElement, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

import "./MarkdownMessage.css";

interface MarkdownMessageProps {
  content: string;
}

interface CodeBlockProps {
  code: string;
  language: string;
}

function CodeBlock({ code, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);

      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (error) {
      console.error("Failed to copy code:", error);
    }
  };

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-language">{language || "code"}</span>

        <button
          type="button"
          className="copy-code-button"
          onClick={() => void handleCopy()}
          aria-label="Copy code"
          title={copied ? "Copied" : "Copy code"}
        >
          {copied ? (
            <span>✓</span>
          ) : (
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="9" y="9" width="13" height="13" rx="2" />

              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
          )}
        </button>
      </div>

      <SyntaxHighlighter
        language={language || "text"}
        style={oneDark}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: 0,
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

function MarkdownMessage({ content }: MarkdownMessageProps) {
  return (
    <div className="markdown-message">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          /*
           * ReactMarkdown renders fenced code blocks
           * inside a <pre> element.
           *
           * Handling <pre> here guarantees that every
           * fenced code block gets our CodeBlock component.
           */
          pre({ children }) {
            const child = children as ReactElement<{
              className?: string;
              children?: ReactNode;
            }>;

            const className = child?.props?.className || "";

            const match = /language-(\w+)/.exec(className);

            const code = String(child?.props?.children ?? "").replace(
              /\n$/,
              "",
            );

            return <CodeBlock code={code} language={match?.[1] || "text"} />;
          },

          /*
           * Inline code remains normal inline code.
           */
          code({ children, ...props }) {
            return <code {...props}>{children}</code>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default MarkdownMessage;
