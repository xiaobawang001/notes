import type { Note } from '~/types/note'

export function useRelatedArticles() {
  function getRelated(currentId: number, allArticles: Note[]): Note[] {
    return allArticles
      .filter((a) => a.id !== currentId && a.type === 'article' && a.status === 'published')
      .slice(0, 5)
  }

  return { getRelated }
}
