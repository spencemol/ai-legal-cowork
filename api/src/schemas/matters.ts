import { z } from 'zod'

export const CreateMatterSchema = z.object({
  title: z.string().min(1),
  case_number: z.string().min(1),
  description: z.string().optional(),
  status: z.enum(['active', 'closed', 'archived']).optional().default('active'),
})

export const UpdateMatterSchema = z.object({
  title: z.string().min(1).optional(),
  case_number: z.string().min(1).optional(),
  description: z.string().optional(),
  status: z.enum(['active', 'closed', 'archived']).optional(),
})

export const CreateAssignmentSchema = z.object({
  user_id: z.string().min(1), // UUID format enforced by DB
  access_level: z.enum(['full', 'restricted', 'read_only']).default('full'),
})

export const CreateClientSchema = z.object({
  name: z.string().min(1),
  contact_email: z.string().email().optional(),
  contact_phone: z.string().optional(),
  address: z.string().optional(),
  role: z.enum(['plaintiff', 'defendant', 'third_party', 'other']).optional().default('other'),
})

export const LinkClientSchema = z.object({
  client_id: z.string().min(1), // UUID format enforced by DB
})
