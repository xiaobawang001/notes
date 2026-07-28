import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', () => {
  // ── 状态 ──
  const fontSize = ref(localStorage.getItem('blog-font-size') || 'medium')
  const contentWidth = ref(localStorage.getItem('blog-content-width') || 'medium')
  const focusMode = ref(localStorage.getItem('blog-focus-mode') === 'true')
  const sidebarOpen = ref(true)
  const darkMode = ref(localStorage.getItem('blog-dark-mode') === 'true')

  // ── 映射表 ──
  const fontSizeMap: Record<string, string> = {
    small: '14px', medium: '16px', large: '18px',
  }
  const widthMap: Record<string, string> = {
    narrow: '720px', medium: '960px', large: '1140px',
  }

  // ── 应用到 DOM ──
  function applySettings() {
    const root = document.documentElement
    // 深浅模式
    if (darkMode.value) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    // 字号
    root.style.setProperty('--blog-doc-font-size', fontSizeMap[fontSize.value] || '16px')
    // 阅读宽度
    root.style.setProperty('--blog-content-max-width', widthMap[contentWidth.value] || '960px')
  }

  // ── 切换方法 ──
  function toggleDarkMode() {
    darkMode.value = !darkMode.value
  }
  function setFontSize(v: string) { fontSize.value = v }
  function setContentWidth(v: string) { contentWidth.value = v }
  function toggleFocusMode() { focusMode.value = !focusMode.value }

  // ── 持久化 & DOM 同步 ──
  watch(fontSize, (v) => { localStorage.setItem('blog-font-size', v); applySettings() })
  watch(contentWidth, (v) => { localStorage.setItem('blog-content-width', v); applySettings() })
  watch(focusMode, (v) => { localStorage.setItem('blog-focus-mode', String(v)); applySettings() })
  watch(darkMode, (v) => { localStorage.setItem('blog-dark-mode', String(v)); applySettings() })

  return {
    fontSize, contentWidth, focusMode, sidebarOpen, darkMode,
    fontSizeMap, widthMap,
    toggleDarkMode, setFontSize, setContentWidth, toggleFocusMode,
    applySettings,
  }
})
