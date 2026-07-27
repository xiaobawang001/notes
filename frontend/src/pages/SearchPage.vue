<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchNotes } from '~/api/notes'
import { NSpin } from 'naive-ui'

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
  <div class="min-h-screen bg-[#f4f5f5] dark:bg-[#2a2b30]">
    <header class="h-14 bg-white dark:bg-[#2c2d32] border-b border-[#e7e9e8] dark:border-[#383940] flex items-center px-5 gap-4">
      <RouterLink to="/" class="text-lg font-semibold text-main no-underline!">我的笔记</RouterLink>
      <div class="flex-1" />
      <input v-model="query" type="text" placeholder="搜索..." class="w-64 px-3 py-1.5 rounded-md border border-[#e7e9e8] dark:border-[#383940] bg-white dark:bg-[#2e2f35] text-14px outline-none text-main" @keydown.enter="doSearch" />
      <button class="text-14px px-3 py-1 rounded bg-[#00b96b]/10 text-[#00b96b] border-none cursor-pointer" @click="doSearch">搜索</button>
    </header>

    <main class="max-w-[960px] mx-auto p-6">
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
