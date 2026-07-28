<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, X, ArrowRight } from 'lucide-vue-next'
import { searchNotes } from '~/api/notes'

const router = useRouter()
const open = ref(false)
const query = ref('')
const results = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

function openModal() {
  open.value = true
  query.value = ''
  results.value = []
  total.value = 0
  nextTick(() => inputRef.value?.focus())
}

function closeModal() {
  open.value = false
  if (debounceTimer) clearTimeout(debounceTimer)
}

async function doSearch() {
  if (!query.value.trim()) { results.value = []; total.value = 0; return }
  loading.value = true
  try {
    const res = await searchNotes(query.value.trim())
    results.value = res.data.items || []
    total.value = res.data.total || 0
  } catch { results.value = []; total.value = 0 }
  finally { loading.value = false }
}

function onQueryChange() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(doSearch, 200)
}

function goToArticle(id: number) {
  closeModal()
  router.push(`/article/${id}`)
}

function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    open.value ? closeModal() : openModal()
    return
  }
  if (e.key === 'Escape' && open.value) { closeModal(); return }
}

function onBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('search-overlay')) closeModal()
}

defineExpose({ openModal })

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => { document.removeEventListener('keydown', onKeydown); if (debounceTimer) clearTimeout(debounceTimer) })
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="search-overlay" @click="onBackdropClick">
      <div class="search-modal">
        <!-- 搜索输入 -->
        <div class="search-input-row">
          <Search :size="18" class="search-icon" />
          <input
            ref="inputRef"
            v-model="query"
            class="search-input"
            placeholder="搜索文章… (Ctrl+K)"
            @input="onQueryChange"
          />
          <kbd class="search-kbd">ESC</kbd>
          <button class="search-close" title="关闭" @click="closeModal"><X :size="16" /></button>
        </div>

        <!-- 搜索结果 -->
        <div class="search-results" v-if="query.trim()">
          <div v-if="loading" class="search-status">搜索中…</div>
          <div v-else-if="results.length === 0" class="search-status">无搜索结果</div>
          <div v-else class="search-result-list">
            <div class="search-total">找到 {{ total }} 条结果</div>
            <button
              v-for="r in results" :key="r.id"
              class="search-result-item"
              @click="goToArticle(r.id)"
            >
              <div class="result-title">{{ r.title }}</div>
              <div class="result-excerpt">{{ r.content?.slice(0, 120) }}</div>
              <div class="result-meta">
                <ArrowRight :size="12" />
                <span>{{ r.word_count }} 字 · {{ new Date(r.updated_at).toLocaleDateString() }}</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  padding-top: 10vh;
}
html.dark .search-overlay { background: rgba(0, 0, 0, 0.6); }
.search-modal {
  width: 560px;
  max-height: 60vh;
  background: var(--yuque-paper-bg);
  border-radius: 10px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
html.dark .search-modal { box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4); }
.search-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--yuque-border-light);
}
.search-icon { color: var(--yuque-text-secondary); flex-shrink: 0; }
.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
  color: var(--yuque-text);
  background: transparent;
}
.search-input::placeholder { color: var(--yuque-text-secondary); }
.search-kbd {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--yuque-border);
  color: var(--yuque-text-secondary);
  background: var(--yuque-page-bg);
  font-family: inherit;
}
.search-close {
  border: none;
  background: none;
  cursor: pointer;
  color: var(--yuque-text-secondary);
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.search-close:hover { color: var(--yuque-text); background: var(--yuque-brand-soft); }
.search-results { overflow-y: auto; flex: 1; }
.search-status { padding: 32px 16px; text-align: center; color: var(--yuque-text-secondary); font-size: 14px; }
.search-total { padding: 10px 16px 4px; font-size: 12px; color: var(--yuque-text-secondary); }
.search-result-list { padding: 4px 8px 12px; }
.search-result-item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  border-radius: 6px;
  padding: 10px 10px;
  cursor: pointer;
  transition: background 0.15s;
}
.search-result-item:hover { background: var(--yuque-brand-soft); }
.result-title { font-size: 14px; font-weight: 600; color: var(--yuque-text); margin-bottom: 2px; }
.result-excerpt { font-size: 13px; color: var(--yuque-text-secondary); line-height: 1.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result-meta { display: flex; align-items: center; gap: 4px; margin-top: 4px; font-size: 12px; color: var(--yuque-text-secondary); }
@media (max-width: 640px) { .search-modal { width: 90vw; } }
</style>
