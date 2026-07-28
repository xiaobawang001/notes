import { authApi } from './client'
import type { TokenResponse } from '~/types/auth'

export function login(username: string, password: string): Promise<{ data: TokenResponse }> {
  return authApi.post('/auth/login', { username, password })
}

export function register(username: string, password: string, email?: string): Promise<{ data: TokenResponse }> {
  return authApi.post('/auth/register', { username, password, email })
}

export function refreshToken(token: string): Promise<{ data: TokenResponse }> {
  return authApi.post('/auth/refresh', { token })
}
