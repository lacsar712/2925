import axios from 'axios'
import { message } from 'ant-design-vue'

const api = axios.create({
  baseURL: '',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bondview_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 401) {
      localStorage.removeItem('bondview_token')
      localStorage.removeItem('bondview_user')
      window.location.href = '/login'
      message.error('登录已过期，请重新登录')
    } else if (status === 403) {
      message.error(detail || '没有权限执行此操作')
    } else if (status === 404) {
      message.error(detail || '请求的资源不存在')
    } else if (status >= 500) {
      message.error('服务器错误，请稍后重试')
    } else {
      message.error(detail || '请求失败')
    }

    return Promise.reject(error)
  }
)

export default api
