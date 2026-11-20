import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  deleteKnowledgeDocument,
  listKnowledgeDocuments,
  uploadKnowledgeDocument,
} from './knowledgeApi'

const mockedFetch = vi.fn()

beforeEach(() => vi.stubGlobal('fetch', mockedFetch))
afterEach(() => {
  mockedFetch.mockReset()
  vi.unstubAllGlobals()
})

describe('knowledge admin API', () => {
  it('includes a bearer token when listing documents', async () => {
    mockedFetch.mockResolvedValue({ ok: true, json: async () => ({ documents: [] }) })
    expect(await listKnowledgeDocuments('test-token')).toEqual({ documents: [] })
    const [url, init] = mockedFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/api/knowledge/documents')
    expect(init.headers).toEqual({ Authorization: 'Bearer test-token' })
    expect(init.method).toBe('GET')
  })

  it('uploads multipart data without forcing a Content-Type header', async () => {
    mockedFetch.mockResolvedValue({ ok: true, json: async () => ({ title: 'Test', chunks_count: 1 }) })
    const file = new File(['# Title\nBody'], 'test.md', { type: 'text/markdown' })
    await uploadKnowledgeDocument('test-token', file, 'Test', 'policy', 'HR')
    const [, init] = mockedFetch.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(init.body).toBeInstanceOf(FormData)
    expect((init.body as FormData).get('file')).toBe(file)
    expect((init.body as FormData).get('kind')).toBe('policy')
    expect(init.headers).toEqual({ Authorization: 'Bearer test-token' })
  })


it('protects original documents from deletion', () => {
  expect(() =>
    deleteKnowledgeDocument('test-token', 'annual-leave')
  ).toThrow('الوثائق الأساسية')

  expect(mockedFetch).not.toHaveBeenCalled()
})

  it('uses DELETE for uploaded documents', async () => {
    mockedFetch.mockResolvedValue({ ok: true, json: async () => ({ status: 'deleted' }) })
    const documentId = `upload-${'a'.repeat(32)}`
    await deleteKnowledgeDocument('test-token', documentId)
    const [url, init] = mockedFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain(documentId)
    expect(init.method).toBe('DELETE')
  })
})
