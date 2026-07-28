<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Search, ArrowUp, ArrowDown, X } from 'lucide-vue-next'
import {
  runInPageSearch, gotoNextMatch, gotoPrevMatch,
  clearInPageSearch, getMatchCount, getCurrentMatchIndex,
} from '~/composables/useInPageSearch'

const route = useRoute()
const open = ref(false)
const query = ref('')
const matchCount = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

const counterText = ref('')

function refreshSearch() {
  matchCount.value = runInPageSearch(query.value)
  counterText.value = !query.value.trim() ? ''
    : !matchCount.value ? '无匹配'
    : `${getCurrentMatchIndex()} / ${matchCount.value}`
}

function openPanel() {
  open.value = true
  nextTick(() => inputRef.value?.focus())
}
function closePanel() {
  open.value = false
  query.value = ''
  clearInPageSearch()
  matchCount.value = 0
  counterText.value = ''
}

function onKeydown(e: KeyboardEvent) {
  // Ctrl+F 触发文内搜索（覆盖浏览器原生查找）
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
    e.preventDefault()
    open.value ? closePanel() : openPanel()
    return
  }
  if (!open.value) return
  if (e.key === 'Escape') { e.preventDefault(); closePanel(); return }
  if (e.key === 'Enter') {
    e.preventDefault()
    if (e.shiftKey) gotoPrevMatch(); else gotoNextMatch()
    matchCount.value = getMatchCount()
    counterText.value = !matchCount.value ? '无匹配' : `${getCurrentMatchIndex()} / ${matchCount.value}`
  }
}

watch(query, () => refreshSearch())
watch(() => route.path, () => closePanel())

onMounted(() => document.addEventListener('keydown', onKeydown, true))
onUnmounted(() => { document.removeEventListener('keydown', onKeydown, true); clearInPageSearch() })
</script>

<template>
  <div class="in-page-search" :class="{ 'is-open': open }">
    <!-- 触发按钮 -->
    <button
      v-show="!open"
      class="w-10 h-10 rounded-[8px] border border-[var(--yuque-border-light)] bg-[var(--yuque-paper-bg)] text-[var(--yuque-text-secondary)] shadow-[var(--yuque-shadow-paper)] cursor-pointer flex items-center justify-center transition-all duration-150 hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] hover:border-[var(--yuque-brand)]"
      title="文内搜索 (Ctrl+F)"
      @click="openPanel"
    >
      <Search :size="18" />
    </button>

    <!-- 搜索面板 -->
    <div v-show="open" class="isp-panel" role="search" aria-label="文内搜索">
      <input
        ref="inputRef"
        v-model="query"
        class="isp-input"
        placeholder="搜索当前页…"
      />
      <span class="isp-counter">{{ counterText }}</span>
      <button class="isp-btn" title="上一个" @click="gotoPrevMatch(); refreshSearch()"><ArrowUp :size="14" /></button>
      <button class="isp-btn" title="下一个" @click="gotoNextMatch(); refreshSearch()"><ArrowDown :size="14" /></button>
      <button class="isp-btn" title="关闭" @click="closePanel"><X :size="14" /></button>
    </div>
  </div>
</template>

<style scoped>
.in-page-search {
  position: fixed;
  right: 24px;
  bottom: 84px;
  z-index: 45;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
.isp-panel {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border: 1px solid var(--yuque-border-light);
  border-radius: 10px;
  background: var(--yuque-paper-bg);
  box-shadow: var(--yuque-shadow-paper);
}
.isp-input {
  width: 180px;
  border: none;
  outline: none;
  font-size: 13px;
  color: var(--yuque-text);
  background: transparent;
  padding: 2px 4px;
}
.isp-input::placeholder { color: var(--yuque-text-secondary); }
.isp-counter {
  min-width: 52px;
  font-size: 12px;
  color: var(--yuque-text-secondary);
  text-align: center;
  white-space: nowrap;
}
.isp-btn {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--yuque-text-secondary);
  transition: all 0.15s;
}
.isp-btn:hover { background: var(--yuque-brand-soft); color: var(--yuque-brand); }
@media (max-width: 767px) {
  .in-page-search { right: 16px; bottom: 76px; }
  .isp-input { width: 140px; }
}
</style>
