<script setup lang="ts">
import { ref, onMounted, computed, provide } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '~/stores/ui'
import { useCategories } from '~/composables/useCategories'
import type { Note, TreeNode } from '~/types/note'
import { getNotes } from '~/api/notes'
import { NSpin } from 'naive-ui'
import { FolderOpen } from 'lucide-vue-next'
import BackToTop from '~/components/BackToTop.vue'
import SiteFooter from '~/components/SiteFooter.vue'
import TreeNodeComp from '~/components/TreeNode.vue'

const router = useRouter()
const ui = useUiStore()
const { listCategories } = useCategories()

const tree = ref<TreeNode[]>([])
const articles = ref<Note[]>([])
const loading = ref(true)

/** 根据 parent_id 查找分类名称 */
function getCategoryName(parentId: number): string {
  for (const cat of tree.value) {
    if (cat.id === parentId) return cat.name
    if (cat.children) {
      for (const child of cat.children) {
        if (child.id === parentId) return child.name
      }
    }
  }
  return ''
}

// 展开/折叠/定位控制（通过 provide/inject 传递给 TreeNode）
const expandAll = ref(false)
const collapseAll = ref(false)
const locateTarget = ref(0)
const locateAncestors = ref(new Set<number>())
const allExpanded = ref(false)
provide('treeExpandAll', expandAll)
provide('treeCollapseAll', collapseAll)
provide('treeLocateTarget', locateTarget)
provide('treeLocateAncestors', locateAncestors)

function toggleAll() {
  allExpanded.value = !allExpanded.value
  if (allExpanded.value) {
    expandAll.value = true; collapseAll.value = false
  } else {
    collapseAll.value = true; expandAll.value = false
  }
  setTimeout(() => { expandAll.value = false; collapseAll.value = false }, 100)
}

/** 在树中查找目标节点的所有祖先 ID */
function findAncestors(nodes: TreeNode[], targetId: number): Set<number> {
  const ancestors = new Set<number>()
  function walk(list: TreeNodeType[], path: number[]): boolean {
    for (const n of list) {
      if (n.id === targetId) { path.forEach(id => ancestors.add(id)); return true }
      if (n.children?.length) {
        path.push(n.id)
        if (walk(n.children, path)) return true
        path.pop()
      }
    }
    return false
  }
  walk(nodes, [])
  return ancestors
}

function doLocate() {
  if (!articles.value.length && !tree.value.length) return
  // 取第一篇文章作为定位目标（首页无当前文章概念，定位到首篇）
  const first = articles.value[0]
  if (!first) return
  locateAncestors.value = findAncestors(tree.value, first.id)
  locateTarget.value = first.id
  setTimeout(() => { locateTarget.value = 0; locateAncestors.value = new Set() }, 500)
}

onMounted(async () => {
  try {
    const [t, res] = await Promise.all([
      listCategories(),
      getNotes({ type: 'article', status: 'published', page_size: 100 }),
    ])
    tree.value = t
    articles.value = res.data.items
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-[var(--yuque-page-bg)]">
    <div class="flex">
      <!-- Sidebar -->
      <aside
        class="sidebar-panel"
        :style="{ visibility: ui.focusMode ? 'hidden' : 'visible' }"
      >
        <div class="p-4 pt-3">
          <!-- 工具栏 -->
          <div class="flex items-center gap-1 mb-3 pb-2 border-b border-[var(--yuque-border-light)]">
            <h2 class="text-15px font-semibold text-[var(--yuque-text)] flex-1">目录</h2>
            <button
              class="w-7 h-7 rounded flex items-center justify-center border-none cursor-pointer text-[var(--yuque-text-secondary)] hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
              title="定位到当前文档"
              @click="doLocate"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4m-10-10h4m12 0h4"/></svg>
            </button>
            <button
              class="w-7 h-7 rounded flex items-center justify-center border-none cursor-pointer text-[var(--yuque-text-secondary)] hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
              :title="allExpanded ? '折叠全部分类' : '展开全部分类'"
              @click="toggleAll"
            >
              <svg v-if="!allExpanded" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"/></svg>
            </button>
          </div>
          <NSpin :show="loading" size="small">
            <TreeNodeComp v-for="node in tree" :key="node.id" :node="node" :level="0" />
          </NSpin>
        </div>
      </aside>

      <!-- Main -->
      <main class="flex-1 ml-[var(--vp-sidebar-width)] min-h-[calc(100vh-56px)]">
        <div class="py-6 flex justify-center">
          <div :style="{ maxWidth: 'var(--blog-content-max-width)', width: '100%' }" class="px-6">
            <h1 class="text-2xl font-bold text-main mb-6">最近文章</h1>
            <NSpin :show="loading">
              <div class="grid gap-3">
                <article
                  v-for="a in articles"
                  :key="a.id"
                  class="paper! p-5 cursor-pointer hover:shadow-md transition-shadow border border-[var(--yuque-border-light)]"
              @click="router.push(`/article/${a.id}`)"
            >
              <h2 class="text-lg font-semibold text-main mb-2 m-0">{{ a.title }}</h2>
              <p class="text-14px text-secondary line-clamp-2 m-0">{{ a.content?.slice(0, 200) }}</p>
              <div class="flex items-center gap-3 mt-3 text-12px text-secondary">
                <span v-if="getCategoryName(a.parent_id)" class="flex items-center gap-1">
                  <FolderOpen :size="12" /> {{ getCategoryName(a.parent_id) }}
                </span>
                <span>{{ a.word_count }} 字</span>
                <span>{{ new Date(a.updated_at).toLocaleDateString() }}</span>
              </div>
            </article>
            </div>
          </NSpin>
        </div>
      </div>
    </main>
    </div>
    <BackToTop />
    <SiteFooter />
  </div>
</template>

<style scoped>
.sidebar-panel {
  position: fixed;
  left: 0;
  top: var(--vp-nav-height, 56px);
  bottom: 0;
  width: var(--vp-sidebar-width, 280px);
  border-right: 1px solid var(--yuque-border);
  background: var(--yuque-sidebar-bg);
  overflow-y: auto;
  z-index: 10;
  transition: visibility 0.2s;
}
</style>
