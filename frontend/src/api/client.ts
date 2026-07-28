import axios, { type AxiosInstance } from 'axios'

// 当前 API 前缀（默认 PostgreSQL，可通过 VITE_API_PREFIX 覆盖）
let currentPrefix = import.meta.env.VITE_API_PREFIX || '/postgre/v1'

// 后端名称 → 前缀映射
const PREFIX_MAP: Record<string, string> = {
  postgres: '/postgre/v1',
  coze: '/coze/v1',
}

/** 创建带统一拦截器的 axios 实例 */
function createApiClient(baseURL: string): AxiosInstance {
  const instance = axios.create({ baseURL, timeout: 15000 })

  // 请求拦截器：自动注入 JWT Token
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // 响应拦截器：统一解包标准响应 + 401 跳转登录
  instance.interceptors.response.use(
    (res) => {
      const payload = res.data
      // 后端标准响应：{ code, data, msg }
      if (payload && typeof payload === 'object' && 'code' in payload && 'data' in payload) {
        res.data = payload.data
        ;(res as any).msg = payload.msg
        ;(res as any).code = payload.code
      }
      return res
    },
    (error) => {
      const status = error.response?.status
      const detail = error.response?.data?.detail || error.response?.data
      if (status === 401 && !window.location.pathname.includes('/login')) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(detail || error)
    },
  )

  return instance
}

// 业务 API：前缀可切换（跟随后端切换）
const api = createApiClient(currentPrefix)

// 认证 API：固定使用 PostgreSQL 前缀（认证不走 Coze）
export const authApi = createApiClient('/postgre/v1')

/** 运行时切换业务 API 前缀（配合 switch-backend 调用后自动更新） */
export function setApiPrefix(backend: string | null) {
  currentPrefix = backend && PREFIX_MAP[backend] ? PREFIX_MAP[backend] : '/postgre/v1'
  api.defaults.baseURL = currentPrefix
  console.log(`[API] 已切换到: ${currentPrefix}`)
}

/** 获取当前业务 API 前缀 */
export function getApiPrefix(): string {
  return currentPrefix
}

export default api
