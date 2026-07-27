import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getNoteById, getNoteBySlug, getNotes, getCategories } from '~/api/notes'
import type { Note, TreeNode } from '~/types/note'

const CACHE_TTL = 5 * 60 * 1000 // 5分钟

interface CacheEntry<T> {
  data: T
  timestamp: number
}

export const useArticlesStore = defineStore('articles', () => {
  const articleCache = ref<Map<string, CacheEntry<Note>>>(new Map())
  const listCache = ref<Map<string, CacheEntry<Note[]>>>(new Map())
  const sidebarTree = ref<TreeNode[] | null>(null)
  const treeTimestamp = ref(0)

  function isExpired(ts: number, ttl: number): boolean {
    return Date.now() - ts > ttl
  }

  async function fetchArticle(idOrSlug: string): Promise<Note> {
    const cacheKey = `article:${idOrSlug}`
    const cached = articleCache.value.get(cacheKey)
    if (cached && !isExpired(cached.timestamp, CACHE_TTL)) {
      return cached.data
    }
    let res: any
    if (/^\d+$/.test(idOrSlug)) {
      res = await getNoteById(Number(idOrSlug))
    } else {
      res = await getNoteBySlug(idOrSlug)
    }
    articleCache.value.set(cacheKey, { data: res.data, timestamp: Date.now() })
    return res.data
  }

  async function fetchList(params?: any): Promise<{ items: Note[]; total: number }> {
    const cacheKey = JSON.stringify(params || {})
    const cached = listCache.value.get(cacheKey)
    if (cached && !isExpired(cached.timestamp, CACHE_TTL)) {
      return { items: cached.data, total: cached.data.length }
    }
    const res = await getNotes(params)
    listCache.value.set(cacheKey, { data: res.data.items, timestamp: Date.now() })
    return { items: res.data.items, total: res.data.total }
  }

  async function fetchSidebarTree(): Promise<TreeNode[]> {
    if (sidebarTree.value && !isExpired(treeTimestamp.value, 10 * 60 * 1000)) {
      return sidebarTree.value
    }
    const res = await getCategories()
    sidebarTree.value = res.data
    treeTimestamp.value = Date.now()
    return res.data
  }

  function invalidateAll() {
    articleCache.value.clear()
    listCache.value.clear()
    sidebarTree.value = null
  }

  return { fetchArticle, fetchList, fetchSidebarTree, invalidateAll }
})
