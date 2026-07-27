<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const query = ref('')
const hasMatches = ref(false)

function search() {
  if (!query.value.trim()) return clearHighlights()
  const text = query.value.trim().toLowerCase()
  const container = document.querySelector('.vp-doc')
  if (!container) return
  clearHighlights()
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT)
  const matches: Range[] = []
  let node
  while ((node = walker.nextNode())) {
    const idx = node.textContent!.toLowerCase().indexOf(text)
    if (idx !== -1) {
      const range = document.createRange()
      range.setStart(node, idx)
      range.setEnd(node, idx + text.length)
      matches.push(range)
    }
  }
  matches.forEach((r, i) => {
    const mark = document.createElement('mark')
    mark.className = 'in-page-highlight'
    if (i === 0) mark.scrollIntoView({ block: 'center', behavior: 'smooth' })
    r.surroundContents(mark)
  })
  hasMatches.value = matches.length > 0
}

function clearHighlights() {
  document.querySelectorAll('.in-page-highlight').forEach((m) => {
    const parent = m.parentNode
    if (parent) {
      parent.replaceChild(document.createTextNode(m.textContent || ''), m)
      parent.normalize()
    }
  })
  hasMatches.value = false
}
</script>

<template>
  <div class="flex items-center gap-2 mb-4">
    <input v-model="query" type="text" placeholder="在文中搜索..." class="w-48 px-3 py-1.5 text-13px rounded-md border border-[#e7e9e8] dark:border-[#383940] bg-white dark:bg-[#2e2f35] text-main outline-none focus:border-[#00b96b]" @keydown.enter="search" @keydown.escape="clearHighlights" />
    <button class="text-12px px-2.5 py-1 rounded bg-[#00b96b]/10 text-[#00b96b] hover:bg-[#00b96b]/20 border-none cursor-pointer" @click="search">搜索</button>
    <button v-if="hasMatches" class="text-12px px-2 py-1 text-[#8a8f8d] border-none bg-transparent cursor-pointer" @click="clearHighlights">清除</button>
  </div>
</template>

<style scoped>
:deep(.in-page-highlight) { background: #ffeb3b; color: #000; border-radius: 2px; padding: 0 1px; }
html.dark :deep(.in-page-highlight) { background: #ffd54f; }
</style>
