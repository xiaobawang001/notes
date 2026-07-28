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
const confirmPassword = ref('')
const email = ref('')
const loading = ref(false)

async function handleRegister() {
  if (username.value.length < 3) { message.warning('用户名至少3个字符'); return }
  if (password.value.length < 6) { message.warning('密码至少6个字符'); return }
  if (password.value !== confirmPassword.value) { message.warning('两次密码输入不一致'); return }
  loading.value = true
  try {
    await auth.register(username.value, password.value, email.value || undefined)
    message.success('注册成功')
    router.push('/notes')
  } catch (e: any) {
    message.error(e?.msg || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#f4f5f5] dark:bg-[#2a2b30]">
    <div class="paper! p-8 w-full max-w-md">
      <h1 class="text-2xl font-bold text-center text-main mb-6">注册</h1>
      <NForm>
        <NFormItem label="用户名"><NInput v-model:value="username" placeholder="至少3个字符" size="large" /></NFormItem>
        <NFormItem label="邮箱（可选）"><NInput v-model:value="email" placeholder="example@email.com" size="large" type="email" /></NFormItem>
        <NFormItem label="密码"><NInput v-model:value="password" type="password" placeholder="至少6个字符" size="large" /></NFormItem>
        <NFormItem label="确认密码"><NInput v-model:value="confirmPassword" type="password" placeholder="再次输入密码" size="large" @keydown.enter="handleRegister" /></NFormItem>
        <NButton type="primary" block size="large" :loading="loading" @click="handleRegister">注册</NButton>
      </NForm>
      <p class="mt-4 text-center text-secondary text-13px">
        已有账号？<RouterLink to="/login" class="link-brand">立即登录</RouterLink>
      </p>
    </div>
  </div>
</template>
