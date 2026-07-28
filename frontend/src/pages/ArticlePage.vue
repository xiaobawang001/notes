<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NTag, NSpin } from 'naive-ui'
import { useMarkdown } from '~/composables/useMarkdown'
import { useArticles } from '~/composables/useArticles'
import { useCategories } from '~/composables/useCategories'
import { useUiStore } from '~/stores/ui'
import type { Note, TreeNode } from '~/types/note'
import ImageZoom from '~/components/ImageZoom.vue'
import NavBreadcrumb from '~/components/NavBreadcrumb.vue'
import InPageSearch from '~/components/InPageSearch.vue'
import DocOutline from '~/components/DocOutline.vue'
import BackToTop from '~/components/BackToTop.vue'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const { render, renderCharts } = useMarkdown()
const { getArticle, listArticles } = useArticles()
const { listCategories } = useCategories()
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
  <div class="min-h-screen bg-[var(--yuque-page-bg)]">
    <div class="flex">
      <!-- Sidebar -->
      <aside
        class="sidebar-panel"
        :style="{ visibility: ui.focusMode ? 'hidden' : 'visible' }"
      >
        <div class="p-4 pt-3">
          <h2 class="text-13px font-semibold text-[var(--yuque-text-secondary)] uppercase mb-3">文章目录</h2>
          <div v-for="node in tree" :key="node.id" class="mb-1">
            <div class="text-14px font-medium text-[var(--yuque-text-secondary)] py-1 px-2">{{ node.name }}</div>
            <div v-if="node.children" class="pl-4">
              <RouterLink
                v-for="child in node.children"
                :key="child.id"
                :to="`/article/${child.id}`"
                class="block py-1 px-2 rounded-md text-13px text-main no-underline! hover:bg-[var(--yuque-brand-soft)]"
                :class="{ 'bg-[var(--yuque-brand-soft)] text-[var(--yuque-brand)]!': child.id === article?.id }"
              >
                {{ child.name }}
              </RouterLink>
            </div>
          </div>
        </div>
      </aside>

      <!-- Content + ToC -->
      <main
        class="flex-1 min-h-screen gap-6 px-6 pt-6"
        :style="{
          marginLeft: ui.focusMode ? '0' : 'var(--vp-sidebar-width)',
          maxWidth: ui.focusMode ? 'var(--blog-content-max-width)' : 'none',
          marginRight: 'auto',
        }"
      >
        <div class="flex gap-6 justify-center">
          <!-- 正文 -->
          <div class="w-full max-w-[var(--blog-content-max-width)]">
            <NSpin :show="loading" size="large">
              <div v-if="error" class="text-center py-16">
                <p class="text-secondary mb-4">文章未找到</p>
                <RouterLink to="/notes" class="link-brand">← 返回首页</RouterLink>
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
                  <article
                    class="vp-doc"
                    :style="{ fontSize: 'var(--blog-doc-font-size)' }"
                    v-html="renderedContent"
                    @click="onContentClick"
                  />
                </div>

                <div class="flex justify-between mt-6 pt-4 border-t border-[var(--yuque-border-light)]">
                  <RouterLink to="/notes" class="link-brand text-14px">← 返回首页</RouterLink>
                </div>
              </template>
            </NSpin>
          </div>

          <!-- 右侧目录（专注模式隐藏） -->
          <div v-if="!ui.focusMode && article">
            <DocOutline content-selector=".vp-doc" />
          </div>
        </div>
      </main>
    </div>

    <BackToTop />
    <ImageZoom :visible="imageVisible" :src="imageSrc" alt="" @update:visible="imageVisible = $event" />
  </div>
</template>

<style scoped>
@import '~/styles/vp-doc.css';

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
