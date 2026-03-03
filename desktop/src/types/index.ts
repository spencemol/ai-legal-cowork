export interface User {
  id: string
  email: string
  name: string
  role: string
}

export interface Matter {
  id: string
  title: string
  caseNumber: string
  status: string
}

export interface Citation {
  doc_id: string
  chunk_id: string
  text_snippet: string
  page: number | null
  // Phase 8: source-typed citation fields (all optional for backward compat)
  source?: 'firm' | 'web' | 'westlaw' | 'lexisnexis'
  url?: string
  title?: string
  citation?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

export interface Conversation {
  id: string
  title: string
  matterId: string
  createdAt: string
}
