<script setup lang="ts">
import { ref, computed, watch, provide, nextTick, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NTag, NSpin, NButton, useMessage } from 'naive-ui'
import { ChevronLeft, ChevronRight, Pencil, Save, X } from 'lucide-vue-next'
import Vditor from 'vditor'
import { useArticles } from '~/composables/useArticles'
import { useCategories } from '~/composables/useCategories'
import { useArticleNav } from '~/composables/useArticleNav'
import { useUiStore } from '~/stores/ui'
import { useAuthStore } from '~/stores/auth'
import { updateNote } from '~/api/notes'
import { renderMarkdown, renderCharts, renderCodeBlocks } from '~/composables/useMarkdown'
import type { Note, TreeNode } from '~/types/note'
import NavBreadcrumb from '~/components/NavBreadcrumb.vue'
import BackToTop from '~/components/BackToTop.vue'
import SiteFooter from '~/components/SiteFooter.vue'
import TreeNodeComp from '~/components/TreeNode.vue'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const auth = useAuthStore()
const message = useMessage()
const { getArticle } = useArticles()
const { listCategories } = useCategories()

const article = ref<Note | null>(null)
const articleId = ref<number | null>(null)
const loading = ref(true)
const error = ref(false)
const tree = ref<TreeNode[]>([])
const activeAncestors = ref(new Set<number>())

// 编辑/预览模式切换
const isEditing = ref(false)
const renderedContent = ref('')
const contentContainer = ref<HTMLElement | null>(null)
const outlineContainer = ref<HTMLElement | null>(null)
let vditorInstance: Vditor | null = null

// 权限判断：只有文章作者本人可编辑
const canEdit = computed(() =>
  auth.isLoggedIn() && article.value?.user_id === auth.user?.id
)

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

// 进入编辑模式（挂载 Vditor 编辑器）
async function enterEdit() {
  destroyVditor()
  isEditing.value = true
  await nextTick()
  const el = document.getElementById('vditor-editor')
  if (!el) return
  vditorInstance = new Vditor(el, {
    mode: 'ir',
    value: article.value?.content || '',
    height: 'auto',
    minHeight: 500,
    toolbar: [
      'headings', 'bold', 'italic', 'strike', '|',
      'quote', 'list', 'ordered-list', 'check', 'code', 'inline-code', 'link', 'table', '|',
      'undo', 'redo', 'fullscreen', 'edit-mode',
    ],
    placeholder: '开始写作...',
    cache: { enable: false },
  })
}

// 销毁 Vditor 实例
function destroyVditor() {
  if (vditorInstance) {
    try { vditorInstance.destroy() } catch { /* ignore */ }
    vditorInstance = null
  }
}

// 保存编辑
async function saveEdit() {
  if (!vditorInstance || !article.value) return
  const content = vditorInstance.getValue()
  try {
    await updateNote(article.value.id, { content })
    article.value.content = content
    message.success('保存成功')
    isEditing.value = false
    destroyVditor()
    await renderContentNow(content)
  } catch {
    message.error('保存失败')
  }
}

// 取消编辑
function cancelEdit() {
  isEditing.value = false
  destroyVditor()
}

// 渲染 Markdown 并刷新代码块 + 图表 + 大纲
async function renderContentNow(content: string) {
  renderedContent.value = await renderMarkdown(content)
  await nextTick()
  if (contentContainer.value) {
    renderCodeBlocks(contentContainer.value)
    renderCharts(contentContainer.value)
    // Vditor outlineRender 遍历直接子元素找 heading（.vp-doc 的内容就是正文）
    if (outlineContainer.value) {
      Vditor.outlineRender(contentContainer.value, outlineContainer.value)
    }
  }
}

async function load() {
  // 切文章时重置编辑状态
  destroyVditor()
  isEditing.value = false
  loading.value = true; error.value = false
  try {
    article.value = await getArticle(idOrSlug.value)
    if (!article.value) { error.value = true; return }
    articleId.value = article.value.id
    const [t] = await Promise.all([listCategories()])
    tree.value = t
    activeAncestors.value = findAncestors(t, article.value.id)
    buildBreadcrumb()
    await renderContentNow(article.value.content)
  } catch { error.value = true } finally { loading.value = false }
}

watch(idOrSlug, load, { immediate: true })

// 组件卸载时清理 Vditor 实例
onBeforeUnmount(() => {
  destroyVditor()
})
</script>

<template>
  <div class="h-[calc(100vh-56px)] bg-[var(--yuque-page-bg)] flex">
    <!-- ===== 左侧目录 ===== -->
    <aside
      class="w-[var(--vp-sidebar-width)] shrink-0 bg-[var(--yuque-sidebar-bg)] border-r border-[var(--yuque-border)] overflow-y-auto sb-hidden"
      :style="{ visibility: ui.focusMode ? 'hidden' : 'visible' }"
    >
      <div class="p-4 pt-3">
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

    <!-- ===== 正文区 ===== -->
    <main class="flex-1 min-w-0 flex flex-col overflow-y-auto">
      <div class="flex-1 w-full mx-auto py-6 px-4" :style="{ maxWidth: 'var(--blog-content-max-width)' }">
        <NSpin :show="loading" size="large">
          <div v-if="error" class="text-center py-16">
            <p class="text-secondary mb-4">文章未找到</p>
            <RouterLink to="/notes" class="link-brand">← 返回首页</RouterLink>
          </div>

          <template v-else-if="article">
            <NavBreadcrumb :items="breadcrumbItems" class="mb-4" />

            <div class="mb-4 flex items-center gap-2 text-13px text-secondary">
              <NTag v-if="article.status === 'draft'" type="error" size="small" round>草稿</NTag>
              <NTag v-if="article.pinned" type="success" size="small" round>置顶</NTag>
              <span>{{ article.word_count }} 字</span>
              <span>更新于 {{ new Date(article.updated_at).toLocaleDateString() }}</span>
            </div>

            <!-- 仅作者可见：编辑/保存/取消按钮 -->
            <div v-if="canEdit" class="flex items-center gap-2 mb-4">
              <NButton v-if="!isEditing" @click="enterEdit" size="small" secondary>
                <template #icon><Pencil :size="14" /></template>
                编辑
              </NButton>
              <template v-else>
                <NButton @click="saveEdit" type="primary" size="small">
                  <template #icon><Save :size="14" /></template>
                  保存
                </NButton>
                <NButton @click="cancelEdit" size="small">
                  <template #icon><X :size="14" /></template>
                  取消
                </NButton>
              </template>
            </div>

            <!-- 预览模式：Vditor 渲染的 Markdown HTML -->
            <div v-if="!isEditing" ref="contentContainer" class="vp-doc" v-html="renderedContent" />

            <!-- 编辑模式：Vditor 编辑器挂载点 -->
            <div v-else id="vditor-editor" class="vditor-editor-wrapper min-h-[400px]" />

            <!-- 临时：正文区内显示 Vditor 原生大纲 -->
            <div v-if="!isEditing" ref="outlineContainer" class="vditor-outline mt-4 p-4 border rounded" />

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
      <SiteFooter />
    </main>

    <!-- ===== 右侧：文章内目录（Vditor outline） ===== -->
    <!-- 暂时隐藏，测试原生 outline 效果 -->
    <!--
    <aside
      v-if="!ui.focusMode && article"
      class="w-[var(--vp-sidebar-width)] shrink-0 bg-[var(--yuque-sidebar-bg)] border-l border-[var(--yuque-border)] overflow-y-auto sb-hidden px-4 pt-4"
    >
      <div class="text-13px font-semibold text-[var(--yuque-text-secondary)] uppercase mb-2 tracking-wider">文章目录</div>
      <div ref="outlineContainer" class="vditor-outline" />
    </aside>
    -->
  </div>
  <BackToTop />
</template>
