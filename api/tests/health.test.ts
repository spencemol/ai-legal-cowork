import { describe, it, expect } from 'vitest'

describe('server bootstrap', () => {
  it('environment is node', () => {
    expect(typeof process).toBe('object')
  })

  it('basic arithmetic works', () => {
    expect(1 + 1).toBe(2)
  })
})
