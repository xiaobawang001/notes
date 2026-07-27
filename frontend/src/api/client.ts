import axios from 'axios'

// 默认使用 PostgreSQL 后端前缀（可通过 VITE_API_PREFIX 覆盖）
const API_PREFIX = import.meta.env.VITE_API_PREFIX || '/postgre/v1'

const api = axios.create({
  baseURL: API_PREFIX,
  timeout: 15000,
})

// 请求拦截器：自动注入 JWT Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一解包标准响应 + 401 跳转登录
api.interceptors.response.use(
  (res) => {
    const payload = res.data
    // 后端标准响应：{ code, data, msg }
    if (payload && typeof payload === 'object' && 'code' in payload && 'data' in payload) {
      // 统一解包，业务侧统一使用 res.data 访问真实数据
      res.data = payload.data
      // 透传提示信息，兼容少量需要读取 msg 的场景
      ;(res as any).msg = payload.msg
      ;(res as any).code = payload.code
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.response?.data
    // 如果是 401，且不在登录页，跳转
    if (status === 401 && !window.location.pathname.includes('/login')) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(detail || error)
  }
)

export default api
