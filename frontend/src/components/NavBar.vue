<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useUiStore } from '~/stores/ui'
import { Sun, Moon, Search, FileText, Settings, LogOut, LogIn } from 'lucide-vue-next'

const auth = useAuthStore()
const ui = useUiStore()

const fontSizeOrder = ['small', 'medium', 'large']
const fontSizeLabel: Record<string, string> = { small: '小', medium: '中', large: '大' }
const widthOrder = ['narrow', 'medium', 'large']
const widthLabel: Record<string, string> = { narrow: '窄', medium: '中', large: '宽' }

const currentFontLabel = computed(() => fontSizeLabel[ui.fontSize] || '中')
const currentWidthLabel = computed(() => widthLabel[ui.contentWidth] || '中')

function cycleFontSize() {
  const idx = fontSizeOrder.indexOf(ui.fontSize)
  ui.setFontSize(fontSizeOrder[(idx + 1) % fontSizeOrder.length])
}
function cycleContentWidth() {
  const idx = widthOrder.indexOf(ui.contentWidth)
  ui.setContentWidth(widthOrder[(idx + 1) % widthOrder.length])
}
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-20 h-14 bg-white dark:bg-[#2c2d32] border-b border-[#e7e9e8] dark:border-[#383940] flex items-center px-5 gap-2 select-none"
  >
    <!-- 站点标题 -->
    <RouterLink to="/" class="text-lg font-semibold text-main no-underline! mr-4">我的笔记</RouterLink>

    <!-- 导航链接 -->
    <RouterLink to="/search" class="flex items-center gap-1 link-brand! text-sm">
      <Search :size="14" /> 搜索
    </RouterLink>

    <div class="flex-1" />

    <!-- 字号切换（轮换：小→中→大→小） -->
    <button
      class="px-2 py-1 text-13px rounded border-none cursor-pointer transition-colors border-r border-[var(--yuque-border)] mr-2"
      :class="'text-secondary hover:bg-[var(--yuque-brand-soft)]'"
      title="点击切换字号"
      @click="cycleFontSize"
    >字 {{ currentFontLabel }}</button>

    <!-- 阅读宽度切换（轮换：窄→中→宽→窄） -->
    <button
      class="px-2 py-1 text-13px rounded border-none cursor-pointer transition-colors border-r border-[var(--yuque-border)] mr-2"
      :class="'text-secondary hover:bg-[var(--yuque-brand-soft)]'"
      title="点击切换阅读宽度"
      @click="cycleContentWidth"
    >宽 {{ currentWidthLabel }}</button>

    <!-- 专注模式 -->
    <button
      class="flex items-center gap-1 px-2 py-1 text-13px rounded border-none cursor-pointer transition-colors mr-2"
      :class="ui.focusMode
        ? 'bg-[#00b96b] text-white'
        : 'text-secondary hover:bg-[#00b96b]/10'"
      title="专注模式"
      @click="ui.toggleFocusMode()"
    >
      <FileText :size="14" />
      <span>专注</span>
    </button>

    <!-- 深色模式 -->
    <button
      class="flex items-center justify-center w-8 h-8 rounded-md border-none cursor-pointer transition-colors"
      :class="ui.darkMode
        ? 'bg-[#00b96b] text-white'
        : 'text-secondary hover:bg-[#00b96b]/10'"
      :title="ui.darkMode ? '切换浅色模式' : '切换深色模式'"
      @click="ui.toggleDarkMode()"
    >
      <Sun v-if="!ui.darkMode" :size="16" />
      <Moon v-else :size="16" />
    </button>

    <!-- 认证 -->
    <template v-if="auth.isLoggedIn()">
      <RouterLink to="/admin" class="flex items-center gap-1 text-sm text-secondary no-underline! hover:text-[#00b96b] ml-2">
        <Settings :size="14" /> 管理
      </RouterLink>
      <button class="flex items-center gap-1 text-sm text-[#8a8f8d] border-none bg-transparent cursor-pointer hover:text-[#00b96b]" @click="auth.logout()">
        <LogOut :size="14" /> 退出
      </button>
    </template>
    <template v-else>
      <RouterLink to="/login" class="flex items-center gap-1 text-sm link-brand! ml-2">
        <LogIn :size="14" /> 登录
      </RouterLink>
    </template>
  </header>
</template>
