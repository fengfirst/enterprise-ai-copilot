import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

type Source = {
  document_id: string;
  source: string;
  distance: number;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  answer: string;
  type?: string;
  tool?: string | null;
  sources?: Source[];
};

type ChatResponse = {
  session_id: string;
  type: string;
  answer: string;
  sources: Source[];
  tool?: string | null;
};

const API_URL = "";

function createSessionId() {
  return `frontend-${crypto.randomUUID()}`;
}

function createMessageId() {
  return crypto.randomUUID();
}

function App() {
  const [sessionId, setSessionId] = useState(createSessionId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const newSession = () => {
    setSessionId(createSessionId());
    setMessages([]);
    setInput("");
    setError("");

    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  };

  const autoResizeTextarea = () => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";

    const nextHeight = Math.min(textarea.scrollHeight, 140);

    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY =
      textarea.scrollHeight > 140 ? "auto" : "hidden";
  };

  useEffect(() => {
    autoResizeTextarea();
  }, [input]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const sendMessage = async () => {
    const message = input.trim();

    if (!message || loading) {
      return;
    }

    setInput("");
    setError("");
    setLoading(true);

    const userMessage: Message = {
      id: createMessageId(),
      role: "user",
      answer: message,
    };

    setMessages((current) => [...current, userMessage]);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          message,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      const assistantMessage: Message = {
        id: createMessageId(),
        role: "assistant",
        answer: data.answer,
        type: data.type,
        tool: data.tool,
        sources: data.sources || [],
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (requestError) {
      console.error(requestError);

      setError(
        "暂时无法连接 AI 服务，请检查后端服务是否正常运行。"
      );
    } finally {
      setLoading(false);

      requestAnimationFrame(() => {
        textareaRef.current?.focus();
      });
    }
  };

  const handleSuggestion = (question: string) => {
    setInput(question);

    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const getTypeLabel = (type?: string) => {
    if (type === "tool") {
      return "TOOL";
    }

    if (type === "rag") {
      return "RAG";
    }

    if (type === "unknown") {
      return "ABSTENTION";
    }

    return type?.toUpperCase() || "";
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">AI</div>

          <div>
            <div className="brand-title">
              Enterprise AI Copilot
            </div>

            <div className="brand-subtitle">
              AI-powered business assistant
            </div>
          </div>
        </div>

        <button
          className="new-session-button"
          onClick={newSession}
          disabled={loading}
        >
          <span className="new-session-icon">+</span>
          <span>New Session</span>
        </button>

        <div className="sidebar-section">
          <div className="sidebar-section-title">
            CURRENT SESSION
          </div>

          <div className="session-card">
            <div className="session-status">
              <span className="status-dot" />
              Active
            </div>

            <div className="session-id">
              {sessionId}
            </div>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="backend-status">
            <span className="status-dot" />
            <span>Backend Connected</span>
          </div>

          <div className="version">
            Enterprise AI Copilot · v0.1.0
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        {/* Header */}
        <header className="header">
          <div>
            <h1>AI Assistant</h1>

            <p>
              Ask about orders, refunds, policies and more.
            </p>
          </div>

          <div className="header-status">
            <span className="status-dot" />
            Online
          </div>
        </header>

        {/* Chat */}
        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✦</div>

              <h2>
                How can I help you?
              </h2>

              <p>
                Ask a question and I&apos;ll route it to the
                right business system or knowledge source.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    handleSuggestion(
                      "帮我查询订单12345的状态",
                    )
                  }
                >
                  查询订单 12345
                </button>

                <button
                  onClick={() =>
                    handleSuggestion(
                      "退款审核通过后一般几天可以到账？",
                    )
                  }
                >
                  查询退款政策
                </button>

                <button
                  onClick={() =>
                    handleSuggestion(
                      "你们公司今年的利润是多少？",
                    )
                  }
                >
                  测试知识库边界
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message) => (
                <div
                  className={`message-row ${message.role}`}
                  key={message.id}
                >
                  <div className="message-avatar">
                    {message.role === "user" ? "You" : "AI"}
                  </div>

                  <div className="message-body">
                    <div className="message-role">
                      {message.role === "user"
                        ? "You"
                        : "Enterprise AI"}
                    </div>

                    <div className="message-bubble">
                      <div className="message-content">
                        {message.role === "assistant" ? (
                          <ReactMarkdown>
                            {message.answer}
                          </ReactMarkdown>
                        ) : (
                          message.answer
                        )}
                      </div>

                      {message.role === "assistant" && (
                        <>
                          {/* Agent metadata */}
                          <div className="metadata">
                            {message.type && (
                              <span
                                className={`type-badge ${message.type}`}
                              >
                                {getTypeLabel(message.type)}
                              </span>
                            )}

                            {message.tool && (
                              <span className="tool-badge">
                                Tool · {message.tool}
                              </span>
                            )}
                          </div>

                          {/* Knowledge sources */}
                          {message.sources &&
                            message.sources.length > 0 && (
                              <details
                                className="sources"
                                open
                              >
                                <summary className="sources-title">
                                  Knowledge Sources ·{" "}
                                  {message.sources.length}
                                </summary>

                                <div className="source-list">
                                  {message.sources.map(
                                    (source) => (
                                      <div
                                        className="source"
                                        key={`${source.document_id}-${source.source}`}
                                      >
                                        <div className="source-main">
                                          <div className="source-name">
                                            {source.source}
                                          </div>

                                          <div className="source-id">
                                            {
                                              source.document_id
                                            }
                                          </div>
                                        </div>

                                        <div className="source-distance">
                                          {source.distance.toFixed(
                                            3,
                                          )}
                                        </div>
                                      </div>
                                    ),
                                  )}
                                </div>
                              </details>
                            )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Loading */}
              {loading && (
                <div className="message-row assistant">
                  <div className="message-avatar">
                    AI
                  </div>

                  <div className="message-body">
                    <div className="message-role">
                      Enterprise AI
                    </div>

                    <div className="message-bubble loading-message">
                      <div className="loading-content">
                        <span className="loading-dot">
                          ●
                        </span>

                        <span className="loading-dot">
                          ●
                        </span>

                        <span className="loading-dot">
                          ●
                        </span>

                        <span className="loading-text">
                          AI 正在处理...
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="composer-area">
          {error && (
            <div className="error-banner">
              <span className="error-icon">!</span>

              <span>{error}</span>

              <button
                onClick={() => setError("")}
                aria-label="关闭错误提示"
              >
                ×
              </button>
            </div>
          )}

          <div className="input-area">
            <div className="input-wrapper">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(event) =>
                  setInput(event.target.value)
                }
                onKeyDown={handleKeyDown}
                placeholder="输入你的问题..."
                disabled={loading}
                rows={1}
              />

              <button
                className="send-button"
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                aria-label="发送"
              >
                ↑
              </button>
            </div>

            <div className="input-hint">
              Enter 发送 · Shift + Enter 换行
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
