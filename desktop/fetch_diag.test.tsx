import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import { useState, useEffect } from 'react'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function TestComp() {
  const [called, setCalled] = useState(false)
  useEffect(() => {
    fetch('http://test/api').then(() => setCalled(true)).catch(() => setCalled(true))
  }, [])
  return <div>{called ? 'done' : 'loading'}</div>
}

describe('fetch diagnostic', () => {
  beforeEach(() => { mockFetch.mockReset() })
  afterEach(() => { cleanup() })

  it('fetch is called in useEffect', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    render(<TestComp />)
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))
    expect(screen.getByText('done')).toBeInTheDocument()
  })
})
