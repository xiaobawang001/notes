<script setup lang="ts">
import { ref, computed, watch, nextTick, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NTag, NSpin } from 'naive-ui'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useMarkdown } from '~/composables/useMarkdown'
import { useArticles } from '~/composables/useArticles'
import { useCategories } from '~/composables/useCategories'
import { useArticleNav } from '~/composables/useArticleNav'
import { useUiStore } from '~/stores/ui'
import type { Note, TreeNode } from '~/types/note'
import ImageZoom from '~/components/ImageZoom.vue'
import NavBreadcrumb from '~/components/NavBreadcrumb.vue'
import InPageSearch from '~/components/InPageSearch.vue'
import DocOutline from '~/components/DocOutline.vue'
import BackToTop from '~/components/BackToTop.vue'
import SiteFooter from '~/components/SiteFooter.vue'
import TreeNodeComp from '~/components/TreeNode.vue'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const { render, renderCharts } = useMarkdown()
const { getArticle } = useArticles()
const { listCategories } = useCategories()
const message = useMessage()

const article = ref<Note | null>(null)
const articleId = ref<number | null>(null)
const loading = ref(true)
const error = ref(false)
const tree = ref<TreeNode[]>([])
const activeAncestors = ref(new Set<number>())
const imageVisible = ref(false)
const imageSrc = ref('')

// 展开/折叠/定位控制
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

function doLocate() {
  if (!article.value) return
  locateAncestors.value = findAncestors(tree.value, article.value.id)
  locateTarget.value = article.value.id
  setTimeout(() => { locateTarget.value = 0; locateAncestors.value = new Set() }, 500)
}

// 上一/下一篇 & 相关推荐
const { prevArticle, nextArticle, relatedArticles } = useArticleNav(tree, articleId)

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
    { label: '首页', to: '/notes' },
    ...path.reverse().map(n => ({ label: n.name, to: n.type === 'article' ? `/article/${n.id}` : undefined })),
  ]
}

/** 在树中查找目标节点的所有祖先 ID */
function findAncestors(nodes: TreeNode[], targetId: number): Set<number> {
  const ancestors = new Set<number>()
  function walk(list: TreeNode[], path: number[]): boolean {
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

async function load() {
  loading.value = true; error.value = false
  try {
    article.value = await getArticle(idOrSlug.value)
    if (!article.value) { error.value = true; return }
    articleId.value = article.value.id
    const [t] = await Promise.all([listCategories()])
    tree.value = t
    activeAncestors.value = findAncestors(t, article.value.id)
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
          <!-- 工具栏 -->
          <div class="flex items-center gap-1 mb-3 pb-2 border-b border-[var(--yuque-border-light)]">
            <h2 class="text-15px font-semibold text-[var(--yuque-text)] flex-1">文章目录</h2>
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
          <TreeNodeComp v-for="node in tree" :key="node.id" :node="node" :level="0" :active-id="article?.id" :ancestor-ids="activeAncestors" />
        </div>
      </aside>

      <!-- Main area -->
      <main
        class="flex-1 ml-[var(--vp-sidebar-width)] min-h-[calc(100vh-56px)]"
        :style="{ marginLeft: ui.focusMode ? '0' : 'var(--vp-sidebar-width)' }"
      >
        <div class="flex gap-8 justify-center px-6 py-6">
          <!-- 正文区 -->
          <div
            class="w-full min-w-0"
            :style="{ maxWidth: ui.focusMode ? 'var(--blog-content-max-width)' : 'var(--blog-content-max-width)' }"
          >
            <NSpin :show="loading" size="large">
              <div v-if="error" class="text-center py-16">
                <p class="text-secondary mb-4">文章未找到</p>
                <RouterLink to="/notes" class="link-brand">← 返回首页</RouterLink>
              </div>

              <template v-else-if="article">
                <NavBreadcrumb :items="breadcrumbItems" />

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

                <!-- 上一篇/下一篇 -->
                <div class="mt-6 pt-4 border-t border-[var(--yuque-border-light)]">
                  <div class="flex justify-between gap-4">
                    <RouterLink
                      v-if="prevArticle"
                      :to="`/article/${prevArticle.id}`"
                      class="flex items-center gap-1 text-14px text-secondary no-underline! hover:text-[var(--yuque-brand)] transition-colors"
                    >
                      <ChevronLeft :size="16" /> {{ prevArticle.title }}
                    </RouterLink>
                    <div v-else />
                    <RouterLink
                      v-if="nextArticle"
                      :to="`/article/${nextArticle.id}`"
                      class="flex items-center gap-1 text-14px text-secondary no-underline! hover:text-[var(--yuque-brand)] transition-colors text-right"
                    >
                      {{ nextArticle.title }} <ChevronRight :size="16" />
                    </RouterLink>
                    <div v-else />
                  </div>
                </div>

                <!-- 相关文章推荐 -->
                <div v-if="relatedArticles.length" class="mt-6 pt-4 border-t border-[var(--yuque-border-light)]">
                  <h3 class="text-15px font-semibold text-main mb-3">相关阅读</h3>
                  <div class="grid grid-cols-2 gap-3">
                    <RouterLink
                      v-for="r in relatedArticles" :key="r.id"
                      :to="`/article/${r.id}`"
                      class="paper! p-4 no-underline! block hover:shadow-md transition-shadow"
                    >
                      <div class="text-14px font-medium text-main mb-1">{{ r.title }}</div>
                      <div class="text-12px text-secondary">{{ r.word_count }} 字</div>
                    </RouterLink>
                  </div>
                </div>
              </template>
            </NSpin>
          </div>

          <!-- 右侧目录 -->
          <div v-if="!ui.focusMode && article" class="shrink-0">
            <DocOutline content-selector=".vp-doc" />
          </div>
        </div>
      </main>
    </div>

    <SiteFooter />
    <InPageSearch />
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
