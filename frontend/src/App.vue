<template>
  <n-config-provider :theme-overrides="themeOverrides" :theme="naiveTheme">
    <n-loading-bar-provider>
      <n-message-provider>
        <!-- 阅读进度条（全局） -->
        <ReadingProgress />
        <!-- 导航栏（登录/注册页不显示） -->
        <NavBar v-if="showNav" />
        <!-- 页面内容：登录/注册页无顶部留白，其余页面 pt-14 为 NavBar 让位 -->
        <div :class="{ 'pt-14': showNav }">
          <router-view />
        </div>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NConfigProvider, NLoadingBarProvider, NMessageProvider, darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import NavBar from '~/components/NavBar.vue'
import ReadingProgress from '~/components/ReadingProgress.vue'
import { useUiStore } from '~/stores/ui'

const route = useRoute()
const ui = useUiStore()

// 登录/注册页不显示 NavBar 和侧边栏
const noNavRoutes = ['Login', 'Register']
const showNav = computed(() => !noNavRoutes.includes(route.name as string))

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#00b96b',
    fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
  },
}

// Naive UI 原生深色模式跟随
const naiveTheme = computed(() => ui.darkMode ? darkTheme : null)

onMounted(() => {
  ui.applySettings()
})
</script>
