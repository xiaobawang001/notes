<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NTag, NSpin, NDivider } from 'naive-ui'
import { useMarkdown } from '~/composables/useMarkdown'
import { useArticles } from '~/composables/useArticles'
import { useCategories } from '~/composables/useCategories'
import type { Note, TreeNode } from '~/types/note'
import ReadingProgress from '~/components/ReadingProgress.vue'
import ImageZoom from '~/components/ImageZoom.vue'
import NavBreadcrumb from '~/components/NavBreadcrumb.vue'
import InPageSearch from '~/components/InPageSearch.vue'
import BackToTop from '~/components/BackToTop.vue'
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const router = useRouter()
const { render, renderCharts } = useMarkdown()
const { getArticle, listArticles } = useArticles()
const { listCategories } = useCategories()
const auth = useAuthStore()
const message = useMessage()

const article = ref<Note | null>(null)
const loading = ref(true)
const error = ref(false)
const tree = ref<TreeNode[]>([])
const imageVisible = ref(false)
const imageSrc = ref('')

const idOrSlug = computed(() => route.params.idOrSlug as string)

const renderedContent = computed(() => render(article.value?.content || ''))

// Breadcrumb
const breadcrumbItems = ref<{ label: string; to?: string }[]>([])

function buildBreadcrumb() {
  if (!article.value) return
  function findPath(nodes: TreeNode[], targetId: number): TreeNode[] {
    for (const n of nodes) {
      if (n.id === targetId) return [n]
      if (n.children?.length) {
        const found = findPath(n.children, targetId)
        if (found.length) return [...found, n]
      }
    }
    return []
  }
  const path = findPath(tree.value, article.value.id)
  breadcrumbItems.value = [
    { label: '首页', to: '/' },
    ...path.reverse().map(n => ({ label: n.name, to: n.type === 'article' ? `/article/${n.id}` : undefined })),
  ]
}

async function load() {
  loading.value = true; error.value = false
  try {
    article.value = await getArticle(idOrSlug.value)
    if (!article.value) { error.value = true; return }
    const [t] = await Promise.all([listCategories()])
    tree.value = t
    buildBreadcrumb()
  } catch { error.value = true } finally { loading.value = false }
}

watch(idOrSlug, load, { immediate: true })

watch(renderedContent, () => {
  nextTick(() => {
    const el = document.querySelector('.vp-doc') as HTMLElement
    if (!el) return
    renderCharts(el)
    const hash = window.location.hash
    if (hash) {
      const target = document.getElementById(hash.slice(1))
      if (target) target.scrollIntoView({ block: 'start' })
    }
  })
})

function onContentClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.classList.contains('heading-anchor')) {
    e.preventDefault()
    const url = `${window.location.origin}${window.location.pathname}${target.getAttribute('href')}`
    navigator.clipboard.writeText(url).then(() => message.success('链接已复制'))
    return
  }
  if (target.tagName === 'IMG' && target.closest('.vp-doc')) {
    imageSrc.value = (target as HTMLImageElement).src
    imageVisible.value = true
    return
  }
  // Code block interactions
  const copyBtn = target.closest('[data-copy]') as HTMLElement | null
  if (copyBtn) {
    const wrapper = copyBtn.closest('.code-block-wrapper') as HTMLElement
    const text = wrapper?.querySelector('.code-body')?.textContent || ''
    navigator.clipboard.writeText(text.trim()).then(() => {
      copyBtn.classList.add('copied')
      const span = copyBtn.querySelector('span')
      if (span) span.textContent = '已复制'
      setTimeout(() => { copyBtn.classList.remove('copied'); if (span) span.textContent = '复制' }, 2000)
    })
    return
  }
  const wrapBtn = target.closest('[data-wrap]') as HTMLElement | null
  if (wrapBtn) { wrapBtn.closest('.code-block-wrapper')?.classList.toggle('wrapped'); return }
  const foldBtn = target.closest('[data-fold]') as HTMLElement | null
  if (foldBtn) { foldBtn.closest('.code-block-wrapper')?.classList.toggle('folded'); return }
}
</script>

<template>
  <ReadingProgress />
  <div class="min-h-screen bg-[#f4f5f5] dark:bg-[#2a2b30]">
    <!-- Nav -->
    <header class="fixed top-0 left-0 right-0 z-20 h-14 bg-white dark:bg-[#2c2d32] border-b border-[#e7e9e8] dark:border-[#383940] flex items-center px-5 gap-4">
      <RouterLink to="/" class="text-lg font-semibold text-main no-underline!">我的笔记</RouterLink>
      <div class="flex-1" />
      <RouterLink to="/" class="link-brand! text-sm">首页</RouterLink>
    </header>

    <div class="flex pt-14">
      <!-- Sidebar -->
      <aside class="fixed left-0 top-14 bottom-0 w-[280px] border-r border-[#e7e9e8] dark:border-[#383940] bg-white dark:bg-[#2c2d32] overflow-y-auto">
        <div class="p-4 pt-3">
          <h2 class="text-13px font-semibold text-[#8a8f8d] uppercase mb-3">文章目录</h2>
          <div v-for="node in tree" :key="node.id" class="mb-1">
            <div class="text-14px font-medium text-[#8a8f8d] py-1 px-2">{{ node.name }}</div>
            <div v-if="node.children" class="pl-4">
              <RouterLink
                v-for="child in node.children"
                :key="child.id"
                :to="`/article/${child.id}`"
                class="block py-1 px-2 rounded-md text-13px text-main no-underline! hover:bg-[#00b96b]/10"
                :class="{ 'bg-[#00b96b]/10 text-[#00b96b]!': child.id === article?.id }"
              >
                {{ child.name }}
              </RouterLink>
            </div>
          </div>
        </div>
      </aside>

      <!-- Content -->
      <main class="flex-1 ml-[280px] flex justify-center">
        <div class="w-full max-w-[960px] px-6 py-6" :style="{ maxWidth: 'var(--blog-content-max-width, 960px)' }">
          <NSpin :show="loading" size="large">
            <div v-if="error" class="text-center py-16">
              <p class="text-secondary mb-4">文章未找到</p>
              <RouterLink to="/" class="link-brand">← 返回首页</RouterLink>
            </div>

            <template v-else-if="article">
              <NavBreadcrumb :items="breadcrumbItems" />
              <InPageSearch v-if="renderedContent" />

              <div class="mb-4 flex items-center gap-2 text-13px text-secondary">
                <NTag v-if="article.status === 'draft'" type="error" size="small" round>草稿</NTag>
                <NTag v-if="article.pinned" type="success" size="small" round>置顶</NTag>
                <span>{{ article.word_count }} 字</span>
                <span>更新于 {{ new Date(article.updated_at).toLocaleDateString() }}</span>
              </div>

              <div class="paper! p-8">
                <article class="vp-doc" v-html="renderedContent" @click="onContentClick" />
              </div>

              <div class="flex justify-between mt-6 pt-4 border-t border-[#eff0f0] dark:border-[#34353b]">
                <RouterLink to="/" class="link-brand text-14px">← 返回首页</RouterLink>
              </div>
            </template>
          </NSpin>
        </div>
      </main>
    </div>

    <back-to-top />
    <ImageZoom :visible="imageVisible" :src="imageSrc" alt="" @update:visible="imageVisible = $event" />
  </div>
</template>

<style scoped>
@import '~/styles/vp-doc.css';
</style>
