<script setup lang="ts">
import { useUiStore } from '~/stores/ui'

const ui = useUiStore()

function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }
</script>

<template>
  <Transition name="fade">
    <div v-if="ui.sidebarOpen" class="fixed bottom-6 right-6 z-40">
      <button class="w-10 h-10 rounded-full bg-white dark:bg-[#3a3b42] shadow-md flex items-center justify-center border border-[#e7e9e8] dark:border-[#383940] cursor-pointer hover:shadow-lg transition-shadow" @click="scrollToTop">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"/></svg>
      </button>
    </div>
  </Transition>
</template>
