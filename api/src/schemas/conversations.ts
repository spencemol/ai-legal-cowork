import { z } from 'zod'

export const CreateConversationSchema = z.object({
  title: z.string().min(1),
})

const CitationSchema = z.object({
  doc_id: z.string().uuid(),
  chunk_id: z.string(),
  text_snippet: z.string(),
  page: z.number().int().nullable().optional(),
  file_name: z.string().optional(),
  source_type: z.enum(['internal', 'web', 'legal_db']).optional(),
})

export const CreateMessageSchema = z.object({
  role: z.enum(['user', 'assistant']),
  content: z.string().min(1),
  citations: z.array(CitationSchema).optional(),
})
