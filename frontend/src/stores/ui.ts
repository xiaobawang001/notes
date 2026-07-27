import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', () => {
  const fontSize = ref(localStorage.getItem('blog-font-size') || 'medium')
  const contentWidth = ref(localStorage.getItem('blog-content-width') || 'medium')
  const focusMode = ref(localStorage.getItem('blog-focus-mode') === 'true')
  const sidebarOpen = ref(true)
  const darkMode = ref(false)

  watch(fontSize, (v) => localStorage.setItem('blog-font-size', v))
  watch(contentWidth, (v) => localStorage.setItem('blog-content-width', v))
  watch(focusMode, (v) => localStorage.setItem('blog-focus-mode', String(v)))

  const fontSizeMap: Record<string, string> = {
    small: '14px', medium: '16px', large: '18px'
  }
  const widthMap: Record<string, string> = {
    narrow: '720px', medium: '960px', large: '1140px'
  }

  return {
    fontSize, contentWidth, focusMode, sidebarOpen, darkMode,
    fontSizeMap, widthMap,
  }
})
