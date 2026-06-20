import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

interface UserInfo {
  id: string
  username: string
  display_name: string
  role: string
  department: string | null
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('bondview_token'))
  const user = ref<UserInfo | null>(null)

  const savedUser = localStorage.getItem('bondview_user')
  if (savedUser) {
    try { user.value = JSON.parse(savedUser) } catch { /* ignore */ }
  }

  async function login(username: string, password: string) {
    const res = await api.post('/api/auth/login', { username, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('bondview_token', res.data.access_token)
    localStorage.setItem('bondview_user', JSON.stringify(res.data.user))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('bondview_token')
    localStorage.removeItem('bondview_user')
  }

  const isAdmin = () => user.value?.role === 'admin'

  return { token, user, login, logout, isAdmin }
})
