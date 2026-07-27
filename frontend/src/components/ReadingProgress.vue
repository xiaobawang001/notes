<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const width = ref(0)
function onScroll() {
  const scrollTop = window.scrollY
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  width.value = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0
}
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <div class="reading-progress"><div class="bar" :style="{ width: `${width}%` }" /></div>
</template>
