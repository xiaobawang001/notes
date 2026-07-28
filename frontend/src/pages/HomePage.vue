<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '~/stores/ui'
import { useCategories } from '~/composables/useCategories'
import type { Note, TreeNode } from '~/types/note'
import { getNotes } from '~/api/notes'
import { NSpin } from 'naive-ui'
import { FolderOpen } from 'lucide-vue-next'
import BackToTop from '~/components/BackToTop.vue'

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
          <h2 class="text-13px font-semibold text-[var(--yuque-text-secondary)] uppercase mb-3">目录</h2>
          <NSpin :show="loading" size="small">
            <div v-for="node in tree" :key="node.id" class="mb-1">
              <div class="flex items-center gap-1.5 py-1 px-2 rounded-md text-14px font-medium text-[var(--yuque-text-secondary)] cursor-default">
                <span>{{ node.name }}</span>
              </div>
              <div v-if="node.children" class="pl-4">
                <RouterLink
                  v-for="child in node.children"
                  :key="child.id"
                  :to="`/article/${child.id}`"
                  class="block py-1.5 px-2 rounded-md text-14px text-main hover:bg-[var(--yuque-brand-soft)] transition-colors no-underline!"
                >
                  {{ child.name }}
                </RouterLink>
              </div>
            </div>
          </NSpin>
        </div>
      </aside>

      <!-- Main -->
      <main class="flex-1 ml-[var(--vp-sidebar-width)] min-h-[calc(100vh-56px)]">
        <div class="mx-auto px-6 py-6" :style="{ maxWidth: 'var(--blog-content-max-width)' }">
          <h1 class="text-2xl font-bold text-main mb-6">最近文章</h1>
          <NSpin :show="loading">
            <div class="grid gap-3">
            <article
              v-for="a in articles"
              :key="a.id"
              class="paper! p-5 cursor-pointer hover:shadow-md transition-shadow"
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
      </main>
    </div>
    <BackToTop />
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
