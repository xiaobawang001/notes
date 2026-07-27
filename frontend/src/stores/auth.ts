import { ref } from 'vue'
import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister } from '~/api/auth'
import type { LoginUser } from '~/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<LoginUser | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    token.value = res.data.token
    localStorage.setItem('token', res.data.token)
    user.value = { id: res.data.user_id, username: res.data.username }
  }

  async function register(username: string, password: string, email?: string) {
    const res = await apiRegister(username, password, email)
    token.value = res.data.token
    localStorage.setItem('token', res.data.token)
    user.value = { id: res.data.user_id, username: res.data.username }
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

  return { user, token, login, register, logout, isLoggedIn }
})
