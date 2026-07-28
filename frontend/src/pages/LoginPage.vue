<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '~/stores/auth'
import { NButton, NInput, NForm, NFormItem, useMessage } from 'naive-ui'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    message.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    message.success('登录成功')
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/notes')
  } catch (e: any) {
    message.error(e?.msg || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#f4f5f5] dark:bg-[#2a2b30]">
    <div class="paper! p-8 w-full max-w-md">
      <h1 class="text-2xl font-bold text-center text-main mb-6">登录</h1>
      <NForm>
        <NFormItem label="用户名"><NInput v-model:value="username" placeholder="请输入用户名" size="large" /></NFormItem>
        <NFormItem label="密码"><NInput v-model:value="password" type="password" placeholder="请输入密码" size="large" @keydown.enter="handleLogin" /></NFormItem>
        <NButton type="primary" block size="large" :loading="loading" @click="handleLogin">登录</NButton>
      </NForm>
      <p class="mt-4 text-center text-secondary text-13px">
        还没有账号？<RouterLink to="/register" class="link-brand">立即注册</RouterLink>
      </p>
    </div>
  </div>
</template>
