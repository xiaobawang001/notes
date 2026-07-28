<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchNotes } from '~/api/notes'
import { NSpin } from 'naive-ui'
import { Search } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const query = ref((route.query.q as string) || '')
const results = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const searched = ref(false)

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true; searched.value = true
  try {
    const res = await searchNotes(query.value.trim())
    results.value = res.data.items; total.value = res.data.total
    router.replace({ query: { q: query.value } })
  } finally { loading.value = false }
}

onMounted(() => { if (query.value) doSearch() })
</script>

<template>
  <div class="min-h-screen bg-[var(--yuque-page-bg)] pt-6">
    <!-- 搜索条 -->
    <div class="max-w-[var(--blog-content-max-width)] mx-auto px-6 pb-4">
      <div class="flex items-center gap-2">
        <Search :size="18" class="text-secondary shrink-0" />
        <input
          v-model="query"
          type="text"
          placeholder="输入关键词搜索文章..."
          class="flex-1 px-4 py-2 text-15px rounded-lg border border-[var(--yuque-border)] bg-[var(--yuque-paper-bg)] outline-none text-main transition-shadow focus:shadow-[0_0_0_2px_var(--yuque-brand-soft)] focus:border-[var(--yuque-brand)]"
          @keydown.enter="doSearch"
        />
        <button
          class="px-5 py-2 text-14px rounded-lg border-none cursor-pointer bg-[var(--yuque-brand)] text-white font-medium hover:opacity-90 transition-opacity"
          @click="doSearch"
        >搜索</button>
      </div>
    </div>

    <main class="max-w-[var(--blog-content-max-width)] mx-auto p-6 pt-0">
      <h1 class="text-xl font-bold text-main mb-4" v-if="searched">搜索结果（{{ total }}）</h1>
      <NSpin :show="loading">
        <div v-if="!searched" class="text-center text-secondary py-16">输入关键词搜索文章</div>
        <div v-else-if="results.length === 0" class="text-center text-secondary py-16">没有找到相关文章</div>
        <div v-else class="grid gap-3">
          <article
            v-for="r in results" :key="r.id"
            class="paper! p-5 cursor-pointer hover:shadow-md transition-shadow"
            @click="router.push(`/article/${r.id}`)"
          >
            <h2 class="text-lg font-semibold text-main mb-2 m-0">{{ r.title }}</h2>
            <p class="text-14px text-secondary line-clamp-2 m-0">{{ r.content?.slice(0, 200) }}</p>
          </article>
        </div>
      </NSpin>
    </main>
  </div>
</template>
