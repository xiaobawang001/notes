import { useArticlesStore } from '~/stores/articles'
import type { Note, NoteListParams } from '~/types/note'

export function useArticles() {
  const store = useArticlesStore()

  async function listArticles(params?: NoteListParams) {
    return store.fetchList(params)
  }

  async function getArticle(idOrSlug: string) {
    return store.fetchArticle(idOrSlug)
  }

  return { listArticles, getArticle }
}
