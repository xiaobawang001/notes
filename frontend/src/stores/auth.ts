import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister } from '~/api/auth'
import type { LoginUser } from '~/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<LoginUser | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  // 还原已登录的用户信息（从 JWT 解析，不触发网络请求）
  function restoreUser() {
    if (token.value && !user.value) {
      try {
        const payload = JSON.parse(atob(token.value.split('.')[1]))
        user.value = { id: parseInt(payload.sub), username: payload.username, role: payload.role || 'user' }
      } catch { /* ignore */ }
    }
  }

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    token.value = res.data.token
    localStorage.setItem('token', res.data.token)
    user.value = { id: res.data.user_id, username: res.data.username, role: res.data.role }
  }

  async function register(username: string, password: string, email?: string) {
    const res = await apiRegister(username, password, email)
    token.value = res.data.token
    localStorage.setItem('token', res.data.token)
    user.value = { id: res.data.user_id, username: res.data.username, role: res.data.role }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    window.location.href = '/'
  }

  function isLoggedIn() {
    return !!token.value
  }

  const isAdmin = computed(() => user.value?.role === 'admin')

  // 初始化时尝试还原用户
  restoreUser()

  return { user, token, login, register, logout, isLoggedIn, isAdmin }
})
