import { z } from 'zod'

export const RegisterDocumentSchema = z.object({
  file_name: z.string().min(1),
  file_path: z.string().min(1),
  file_size: z.number().int().positive(),
  mime_type: z.string().min(1),
  sha256_hash: z.string().min(1),
})

export const UpdateDocumentStatusSchema = z.object({
  status: z.enum(['pending', 'processing', 'indexed', 'failed']),
})
