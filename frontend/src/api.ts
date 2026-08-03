import type { ChatResponse } from './types'

export async function askQuestion(message: string, topK = 5, audience?: string): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, top_k: topK, audience: audience || null }),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail || `Request failed with status ${res.status}`
    throw new Error(detail)
  }

  return res.json()
}
