import api from './client'
import type { Note, NoteListParams } from '~/types/note'
import type { PaginatedData } from '~/types/common'

export function getNotes(params?: NoteListParams): Promise<{ data: PaginatedData<Note> }> {
  return api.get('/notes', { params })
}

export function getNoteById(id: number): Promise<{ data: Note }> {
  return api.get(`/notes/${id}`)
}

export function getNoteBySlug(slug: string): Promise<{ data: Note }> {
  return api.get(`/notes/slug/${slug}`)
}

export function createNote(data: Partial<Note>): Promise<{ data: Note }> {
  return api.post('/notes', data)
}

export function updateNote(id: number, data: Partial<Note>): Promise<{ data: Note }> {
  return api.put(`/notes/${id}`, data)
}

export function deleteNote(id: number): Promise<{ data: {} }> {
  return api.delete(`/notes/${id}`)
}

export function getCategories(): Promise<{ data: any[] }> {
  return api.get('/notes/categories')
}

export function searchNotes(q: string): Promise<{ data: { items: any[]; total: number } }> {
  return api.get('/notes/search', { params: { q } })
}
