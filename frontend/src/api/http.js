import axios from 'axios'
import { ElMessage } from 'element-plus'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const http = axios.create({
  baseURL,
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('pyoffer_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const data = error.response?.data
    const message = data?.message || data?.detail || error.message || '请求失败'

    if (status === 401) {
      localStorage.removeItem('pyoffer_token')
      localStorage.removeItem('pyoffer_user')
      if (window.location.pathname !== '/auth') {
        window.location.href = '/auth'
      }
    } else {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  },
)

export function toFormData(payload) {
  const formData = new FormData()
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      formData.append(key, value)
    }
  })
  return formData
}
