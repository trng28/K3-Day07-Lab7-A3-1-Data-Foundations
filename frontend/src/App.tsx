import { useEffect, useRef, useState } from 'react'
import { Bot, ExternalLink, FileText, LoaderCircle, Send, Sparkles, UserRound } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'
import { askQuestion } from './api'
import type { ChatMessage } from './types'

const SUGGESTIONS = [
  'Các loại học bổng tại VinUni?',
  'Học phí các chương trình đại học là bao nhiêu?',
  'Sinh viên được chuyển đổi tối đa bao nhiêu tín chỉ?',
]

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [audience, setAudience] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendQuestion(question: string) {
    const value = question.trim()
    if (!value || loading) return
    setMessages((current) => [...current, { id: makeId(), role: 'user', content: value }])
    setInput('')
    setLoading(true)

    try {
      const response = await askQuestion(value, 5, audience || undefined)
      setMessages((current) => [
        ...current,
        { id: makeId(), role: 'assistant', content: response.answer, citations: response.citations },
      ])
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Không thể xử lý câu hỏi lúc này.'
      setMessages((current) => [
        ...current,
        { id: makeId(), role: 'assistant', content: detail, isError: true },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="chat-app">
      <header className="chat-header">
        <div className="brand-mark"><Bot /></div>
        <div>
          <h1>Dịch Vụ Đại học - AI Assistant</h1>
          <span><i /> Trợ lý đang hoạt động</span>
        </div>
      </header>

      <main className="chat-scroll">
        {messages.length === 0 && (
          <section className="chat-hero">
            <div className="hero-bot"><Bot /></div>
            <span><Sparkles /> Trợ lý thông tin có kiểm chứng</span>
            <h2>Chào bạn, mình có thể giúp gì?</h2>
            <p>
              Đặt câu hỏi về quy định và dịch vụ đại học VinUniversity. Câu trả lời được
              tổng hợp từ kho tài liệu và luôn đi kèm nguồn tham khảo.
            </p>
            <div className="suggestions">
              {SUGGESTIONS.map((suggestion) => (
                <button key={suggestion} onClick={() => void sendQuestion(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          </section>
        )}

        <div className="turn-list">
          {messages.map((message) => (
            <article className={`message-row ${message.role}`} key={message.id}>
              <div className="avatar">{message.role === 'user' ? <UserRound /> : <Bot />}</div>
              <div className="message-content">
                <span>{message.role === 'user' ? 'Bạn' : 'AI Assistant'}</span>
                {message.role === 'assistant' ? (
                  <div className={`assistant-answer ${message.isError ? 'error' : ''}`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                  </div>
                ) : (
                  <div className="user-bubble">{message.content}</div>
                )}

                {!!message.citations?.length && (
                  <section className="source-panel">
                    <header><FileText /> Nguồn trích dẫn ({message.citations.length})</header>
                    {message.citations.map((citation) => (
                      <article key={`${message.id}-${citation.index}`}>
                        <div>
                          <strong>[{citation.index}] {citation.title}</strong>
                          {citation.snippet && <p>{citation.snippet}</p>}
                          <small>
                            {citation.category || 'Tài liệu chính thức'} · độ tương đồng {citation.score.toFixed(3)}
                          </small>
                        </div>
                        {citation.source_url && (
                          <a href={citation.source_url} target="_blank" rel="noreferrer" aria-label="Mở nguồn">
                            <ExternalLink />
                          </a>
                        )}
                      </article>
                    ))}
                  </section>
                )}
              </div>
            </article>
          ))}

          {loading && (
            <article className="message-row assistant">
              <div className="avatar"><Bot /></div>
              <div className="message-content">
                <span>AI Assistant</span>
                <div className="thinking-card">
                  <LoaderCircle className="spin" />
                  <div><b>Đang phân tích tài liệu...</b><small>Hiểu truy vấn · Truy xuất · Tổng hợp nguồn</small></div>
                </div>
              </div>
            </article>
          )}
          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="composer-area">
        <form onSubmit={(event) => { event.preventDefault(); void sendQuestion(input) }}>
          <select value={audience} onChange={(event) => setAudience(event.target.value)} aria-label="Lọc đối tượng">
            <option value="">Mọi đối tượng</option>
            <option value="student">Sinh viên</option>
            <option value="all">Tất cả</option>
          </select>
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                void sendQuestion(input)
              }
            }}
            placeholder="Nhập câu hỏi về dịch vụ và quy định VinUni..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} aria-label="Gửi câu hỏi">
            {loading ? <LoaderCircle className="spin" /> : <Send />}
          </button>
        </form>
        <small>AI có thể mắc lỗi. Vui lòng đối chiếu tài liệu chính thức.</small>
      </footer>
    </div>
  )
}

export default App
