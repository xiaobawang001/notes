import { useArticlesStore } from '~/stores/articles'

export function useCategories() {
  const store = useArticlesStore()
  return { listCategories: () => store.fetchSidebarTree() }
}
