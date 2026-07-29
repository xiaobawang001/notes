<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

interface TocItem {
  id: string
  text: string
  level: number
}

const props = defineProps<{ contentSelector?: string }>()

const items = ref<TocItem[]>([])
const activeId = ref('')
let observer: IntersectionObserver | null = null

function scanHeadings() {
  const container = document.querySelector(props.contentSelector || '.vp-doc')
  if (!container) { items.value = []; return }
  const headings = container.querySelectorAll('h2, h3, h4')
  items.value = Array.from(headings)
    .filter(h => h.id)
    .map(h => ({
      id: h.id,
      text: (h as HTMLElement).innerText || '',
      level: parseInt(h.tagName[1]),
    }))
  setupIntersection()
}

function setupIntersection() {
  if (observer) observer.disconnect()
  const container = document.querySelector(props.contentSelector || '.vp-doc')
  if (!container) return
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          activeId.value = entry.target.id
        }
      }
    },
    { rootMargin: '-80px 0px -60% 0px', threshold: 0 },
  )
  container.querySelectorAll('h2, h3, h4').forEach(h => {
    if (h.id) observer?.observe(h)
  })
}

function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeId.value = id
  }
}

watch(() => items.value.length, () => {
  // 内容变化后重设 IntersectionObserver
})

defineExpose({ scanHeadings })

onMounted(() => {
  nextTick(() => scanHeadings())
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<template>
  <aside
    v-if="items.length"
    class="toc-wrapper"
  >
    <div class="toc-title">文章目录</div>
    <nav class="toc-list">
      <a
        v-for="item in items"
        :key="item.id"
        :href="`#${item.id}`"
        :class="[
          'toc-link',
          `toc-level-${item.level}`,
          { 'toc-active': activeId === item.id },
        ]"
        @click.prevent="scrollTo(item.id)"
      >{{ item.text }}</a>
    </nav>
    <div v-if="!items.length" class="toc-empty">无目录</div>
  </aside>
</template>

<style scoped>
.toc-wrapper {
  position: sticky;
  top: calc(var(--vp-nav-height, 56px) + 24px);
  width: var(--vp-sidebar-width, 280px);
  max-height: calc(100vh - var(--vp-nav-height, 56px) - 48px);
  overflow-y: auto;
  flex-shrink: 0;
}
.toc-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--yuque-text-secondary);
  text-transform: uppercase;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}
.toc-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.toc-link {
  display: block;
  font-size: 13px;
  line-height: 1.5;
  padding: 3px 8px;
  border-radius: 4px;
  color: var(--yuque-text-secondary);
  text-decoration: none;
  transition: all 0.15s;
  border-left: 2px solid transparent;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.toc-link:hover {
  color: var(--yuque-brand);
  background: var(--yuque-brand-soft);
}
.toc-link.toc-active {
  color: var(--yuque-brand);
  border-left-color: var(--yuque-brand);
  background: var(--yuque-brand-soft);
  font-weight: 500;
}
.toc-level-3 { padding-left: 20px; font-size: 12.5px; }
.toc-level-4 { padding-left: 32px; font-size: 12px; }
.toc-empty {
  font-size: 13px;
  color: var(--yuque-text-secondary);
  padding: 8px;
}
</style>
