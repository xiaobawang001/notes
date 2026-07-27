export interface Note {
  id: number
  user_id: number
  type: 'folder' | 'article'
  title: string
  slug: string
  content: string
  parent_id: number
  status: 'draft' | 'published'
  pinned: boolean
  sort_order: number
  word_count: number
  created_at: string
  updated_at: string
}

export interface NoteListParams {
  type?: 'folder' | 'article'
  status?: 'draft' | 'published'
  parent_id?: number
  search?: string
  page?: number
  page_size?: number
}

export interface TreeNode {
  id: number
  type: string
  name: string
  slug: string
  parent_id: number
  children?: TreeNode[]
}
