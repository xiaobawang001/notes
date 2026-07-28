<template>
  <n-config-provider :theme-overrides="themeOverrides" :theme="naiveTheme">
    <n-loading-bar-provider>
      <n-message-provider>
        <!-- 阅读进度条（全局） -->
        <ReadingProgress />
        <!-- 导航栏（共用） -->
        <NavBar />
        <!-- 页面内容 -->
        <div class="pt-14">
          <router-view />
        </div>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { NConfigProvider, NLoadingBarProvider, NMessageProvider, darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import NavBar from '~/components/NavBar.vue'
import ReadingProgress from '~/components/ReadingProgress.vue'
import { useUiStore } from '~/stores/ui'

const ui = useUiStore()

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
