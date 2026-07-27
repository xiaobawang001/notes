import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
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

// 响应拦截器：401 跳转登录
api.interceptors.response.use(
  (res) => res,
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
