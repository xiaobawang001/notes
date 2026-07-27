<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '~/stores/auth'
import { useCategories } from '~/composables/useCategories'
import type { Note, TreeNode } from '~/types/note'
import { getNotes, getCategories } from '~/api/notes'
import { NSpin } from 'naive-ui'
import BackToTop from '~/components/BackToTop.vue'
import ReadingProgress from '~/components/ReadingProgress.vue'

const router = useRouter()
const auth = useAuthStore()
const { listCategories } = useCategories()

const tree = ref<TreeNode[]>([])
const articles = ref<Note[]>([])
const loading = ref(true)
const selectedId = ref<number | null>(null)

onMounted(async () => {
  try {
    const [t, res] = await Promise.all([listCategories(), getNotes({ type: 'article', status: 'published', page_size: 100 })])
    tree.value = t
    articles.value = res.data.items
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <ReadingProgress />
  <div class="min-h-screen bg-[#f4f5f5] dark:bg-[#2a2b30]">
    <!-- Nav -->
    <header class="fixed top-0 left-0 right-0 z-20 h-14 bg-white dark:bg-[#2c2d32] border-b border-[#e7e9e8] dark:border-[#383940] flex items-center px-5 gap-4">
      <h1 class="text-lg font-semibold text-main m-0">我的笔记</h1>
      <div class="flex-1" />
      <template v-if="auth.isLoggedIn()">
        <RouterLink to="/admin" class="link-brand! text-sm">管理</RouterLink>
        <button class="text-sm text-[#8a8f8d] dark:text-[#76777d] border-none bg-transparent cursor-pointer" @click="auth.logout()">退出</button>
      </template>
      <template v-else>
        <RouterLink to="/login" class="link-brand! text-sm">登录</RouterLink>
      </template>
    </header>

    <div class="flex pt-14">
      <!-- Sidebar -->
      <aside class="fixed left-0 top-14 bottom-0 w-[280px] border-r border-[#e7e9e8] dark:border-[#383940] bg-white dark:bg-[#2c2d32] overflow-y-auto">
        <div class="p-4 pt-3">
          <h2 class="text-13px font-semibold text-[#8a8f8d] dark:text-[#76777d] uppercase mb-3">目录</h2>
          <NSpin :show="loading" size="small">
            <div v-for="node in tree" :key="node.id" class="mb-1">
              <div class="flex items-center gap-1.5 py-1 px-2 rounded-md text-14px font-medium text-[#8a8f8d] cursor-default">
                <span>{{ node.name }}</span>
              </div>
              <div v-if="node.children" class="pl-4">
                <RouterLink
                  v-for="child in node.children"
                  :key="child.id"
                  :to="`/article/${child.id}`"
                  class="block py-1.5 px-2 rounded-md text-14px text-main hover:bg-[#00b96b]/10 transition-colors no-underline!"
                >
                  {{ child.name }}
                </RouterLink>
              </div>
            </div>
          </NSpin>
        </div>
      </aside>

      <!-- Main -->
      <main class="flex-1 ml-[280px] p-6 max-w-[960px]">
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
              <div class="flex items-center gap-2 mt-3 text-12px text-secondary">
                <span>{{ a.word_count }} 字</span>
                <span>{{ new Date(a.updated_at).toLocaleDateString() }}</span>
              </div>
            </article>
          </div>
        </NSpin>
      </main>
    </div>
    <BackToTop />
  </div>
</template>
