<script setup lang="ts">
import { computed } from 'vue'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '~/stores/auth'
import { useUiStore } from '~/stores/ui'
import {
  Search, Type, StretchHorizontal, ScanEye, Sun, Moon,
  Settings, LogOut, LogIn,
} from 'lucide-vue-next'

const auth = useAuthStore()
const ui = useUiStore()
const message = useMessage()

const fontSizeOrder = ['small', 'medium', 'large']
const fontSizeLabel: Record<string, string> = { small: '小', medium: '中', large: '大' }
const widthOrder = ['narrow', 'medium', 'large']
const widthLabel: Record<string, string> = { narrow: '窄', medium: '中', large: '宽' }

const currentFontLabel = computed(() => fontSizeLabel[ui.fontSize])
const currentWidthLabel = computed(() => widthLabel[ui.contentWidth])

function cycleFontSize() {
  const idx = fontSizeOrder.indexOf(ui.fontSize)
  const next = fontSizeOrder[(idx + 1) % fontSizeOrder.length]
  ui.setFontSize(next)
  message.success(`字号：${fontSizeLabel[next]}`)
}
function cycleContentWidth() {
  const idx = widthOrder.indexOf(ui.contentWidth)
  const next = widthOrder[(idx + 1) % widthOrder.length]
  ui.setContentWidth(next)
  message.success(`宽度：${widthLabel[next]}`)
}
function toggleFocus() {
  ui.toggleFocusMode()
  message.success(ui.focusMode ? '专注模式已开启' : '专注模式已关闭')
}
function toggleDark() {
  ui.toggleDarkMode()
  message.success(ui.darkMode ? '深色模式已开启' : '浅色模式已开启')
}
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-20 h-14 bg-white dark:bg-[#2c2d32] border-b border-[#e7e9e8] dark:border-[#383940] flex items-center px-5 gap-1 select-none"
  >
    <!-- 站点标题 -->
    <RouterLink to="/" class="text-lg font-semibold text-main no-underline! mr-3">我的笔记</RouterLink>

    <!-- 搜索 -->
    <RouterLink
      to="/search"
      class="flex items-center justify-center w-8 h-8 rounded-md text-secondary no-underline! hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
      title="搜索"
    >
      <Search :size="16" />
    </RouterLink>

    <div class="flex-1" />

    <!-- 控制按钮组：统一 w-8 h-8 rounded-md border-none cursor-pointer flex-center -->
    <button
      class="w-8 h-8 rounded-md border-none cursor-pointer flex items-center justify-center text-secondary hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
      :title="`字号：${currentFontLabel}（点击切换）`"
      @click="cycleFontSize"
    >
      <Type :size="16" />
    </button>

    <button
      class="w-8 h-8 rounded-md border-none cursor-pointer flex items-center justify-center text-secondary hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
      :title="`阅读宽度：${currentWidthLabel}（点击切换）`"
      @click="cycleContentWidth"
    >
      <StretchHorizontal :size="16" />
    </button>

    <button
      class="w-8 h-8 rounded-md border-none cursor-pointer flex items-center justify-center transition-colors"
      :class="ui.focusMode
        ? 'bg-[var(--yuque-brand-soft)] text-[var(--yuque-brand)]'
        : 'text-secondary hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)]'"
      title="专注模式：隐藏侧边栏和目录"
      @click="toggleFocus"
    >
      <ScanEye :size="16" />
    </button>

    <button
      class="w-8 h-8 rounded-md border-none cursor-pointer flex items-center justify-center transition-colors"
      :class="ui.darkMode
        ? 'bg-[var(--yuque-brand-soft)] text-[var(--yuque-brand)]'
        : 'text-secondary hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)]'"
      :title="ui.darkMode ? '切换浅色模式' : '切换深色模式'"
      @click="toggleDark"
    >
      <Sun v-if="!ui.darkMode" :size="16" />
      <Moon v-else :size="16" />
    </button>

    <!-- 认证 -->
    <template v-if="auth.isLoggedIn()">
      <div class="w-px h-5 bg-[var(--yuque-border)] mx-1" />
      <RouterLink
        to="/admin"
        class="w-8 h-8 rounded-md flex items-center justify-center text-secondary no-underline! hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
        title="管理后台"
      >
        <Settings :size="16" />
      </RouterLink>
      <button
        class="w-8 h-8 rounded-md border-none cursor-pointer flex items-center justify-center text-secondary hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
        title="退出登录"
        @click="auth.logout()"
      >
        <LogOut :size="16" />
      </button>
    </template>
    <template v-else>
      <div class="w-px h-5 bg-[var(--yuque-border)] mx-1" />
      <RouterLink
        to="/login"
        class="w-8 h-8 rounded-md flex items-center justify-center text-secondary no-underline! hover:bg-[var(--yuque-brand-soft)] hover:text-[var(--yuque-brand)] transition-colors"
        title="登录"
      >
        <LogIn :size="16" />
      </RouterLink>
    </template>
  </header>
</template>
