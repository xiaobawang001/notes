<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const visible = ref(false)
let scrollTimer: ReturnType<typeof setTimeout> | null = null

function onScroll() {
  if (scrollTimer) return
  scrollTimer = setTimeout(() => {
    visible.value = window.scrollY > 300
    scrollTimer = null
  }, 100)
}

function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => { window.removeEventListener('scroll', onScroll); if (scrollTimer) clearTimeout(scrollTimer) })
</script>

<template>
  <Transition name="fade">
    <button
      v-if="visible"
      class="fixed z-40 flex items-center justify-center border-none cursor-pointer transition-all duration-150"
      :style="{ right: '24px', bottom: '32px' }"
      :class="[
        'w-10 h-10 rounded-[8px]',
        'bg-[var(--yuque-paper-bg)] text-[var(--yuque-text-secondary)]',
        'border border-[var(--yuque-border-light)]',
        'shadow-[var(--yuque-shadow-paper)]',
        'hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] hover:border-[var(--yuque-brand)]',
      ]"
      title="回到顶部"
      @click="scrollToTop"
    >
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"/></svg>
    </button>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
