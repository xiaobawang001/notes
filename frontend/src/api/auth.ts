import api from './client'
import type { TokenResponse } from '~/types/auth'

export function login(username: string, password: string): Promise<{ data: TokenResponse }> {
  return api.post('/auth/login', { username, password })
}

export function register(username: string, password: string, email?: string): Promise<{ data: TokenResponse }> {
  return api.post('/auth/register', { username, password, email })
}

export function refreshToken(token: string): Promise<{ data: TokenResponse }> {
  return api.post('/auth/refresh', { token })
}
