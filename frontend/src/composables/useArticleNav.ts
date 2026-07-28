import { computed, ref, watch, onMounted } from 'vue'
import { getNotes } from '~/api/notes'
import type { Note, TreeNode } from '~/types/note'

/** 获取当前文章的上一篇/下一篇以及同分类文章列表（用于相关推荐） */
export function useArticleNav(tree: ReturnType<typeof ref<TreeNode[]>>, articleId: ReturnType<typeof ref<number | null>>) {
  const allArticles = ref<Note[]>([])
  const loading = ref(false)

  // 加载全量已发布文章
  async function loadArticles() {
    loading.value = true
    try {
      const res = await getNotes({ type: 'article', status: 'published', page_size: 200 })
      allArticles.value = res.data.items || []
    } catch { /* ignore */ } finally { loading.value = false }
  }

  // 当前文章在树中的位置
  const flatList = computed(() => {
    const list: { id: number; title: string }[] = []
    function walk(nodes: TreeNode[]) {
      for (const n of nodes) {
        if (n.type === 'article') {
          list.push({ id: n.id, title: n.name })
        }
        if (n.children?.length) walk(n.children)
      }
    }
    walk(tree.value)
    return list
  })

  const currentIdx = computed(() => flatList.value.findIndex(a => a.id === articleId.value))
  const prevArticle = computed(() => currentIdx.value > 0 ? flatList.value[currentIdx.value - 1] : null)
  const nextArticle = computed(() =>
    currentIdx.value >= 0 && currentIdx.value < flatList.value.length - 1
      ? flatList.value[currentIdx.value + 1]
      : null,
  )

  // 相关推荐：同分类其他文章（最多 5 篇）
  const relatedArticles = computed(() => {
    return allArticles.value
      .filter(a => a.id !== articleId.value && a.type === 'article' && a.status === 'published')
      .slice(0, 5)
  })

  onMounted(() => { loadArticles() })

  return { prevArticle, nextArticle, relatedArticles, allArticles, loading }
}
