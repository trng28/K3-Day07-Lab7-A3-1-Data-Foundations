export interface Citation {
  index: number
  doc_id: string
  title: string
  source_url: string
  category: string | null
  audience: string | null
  score: number
  snippet: string
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  isError?: boolean
}
