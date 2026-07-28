<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
import { useUiStore } from '~/stores/ui'
import { useRouter } from 'vue-router'
import { Sun, Moon, Search, FileText, Settings, LogOut, LogIn } from 'lucide-vue-next'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()

const fontSizeOptions = [
  { label: '小', value: 'small' },
  { label: '中', value: 'medium' },
  { label: '大', value: 'large' },
]
const widthOptions = [
  { label: '窄', value: 'narrow' },
  { label: '中', value: 'medium' },
  { label: '宽', value: 'large' },
]
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

    <!-- 字号切换 -->
    <div class="flex items-center gap-0.5 border-r border-[#e7e9e8] dark:border-[#383940] pr-2 mr-2">
      <button
        v-for="opt in fontSizeOptions" :key="opt.value"
        class="px-1.5 py-0.5 text-13px rounded border-none cursor-pointer transition-colors"
        :class="ui.fontSize === opt.value
          ? 'bg-[#00b96b] text-white'
          : 'text-secondary hover:bg-[#00b96b]/10'"
        :title="`字号：${opt.label}`"
        @click="ui.setFontSize(opt.value)"
      >{{ opt.label }}</button>
    </div>

    <!-- 阅读宽度切换 -->
    <div class="flex items-center gap-0.5 border-r border-[#e7e9e8] dark:border-[#383940] pr-2 mr-2">
      <button
        v-for="opt in widthOptions" :key="opt.value"
        class="px-1.5 py-0.5 text-13px rounded border-none cursor-pointer transition-colors"
        :class="ui.contentWidth === opt.value
          ? 'bg-[#00b96b] text-white'
          : 'text-secondary hover:bg-[#00b96b]/10'"
        :title="`阅读宽度：${opt.label}`"
        @click="ui.setContentWidth(opt.value)"
      >{{ opt.label }}</button>
    </div>

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
