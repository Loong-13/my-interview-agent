import { defineStore } from 'pinia'

import { authApi } from '@/api/modules'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('pyoffer_token') || '',
    user: JSON.parse(localStorage.getItem('pyoffer_user') || 'null'),
  }),
  getters: {
    isAuthed: (state) => Boolean(state.token),
  },
  actions: {
    persist() {
      if (this.token) {
        localStorage.setItem('pyoffer_token', this.token)
      } else {
        localStorage.removeItem('pyoffer_token')
      }
      if (this.user) {
        localStorage.setItem('pyoffer_user', JSON.stringify(this.user))
      } else {
        localStorage.removeItem('pyoffer_user')
      }
    },
    async login(payload) {
      const token = await authApi.login(payload)
      this.token = token.access_token
      await this.fetchMe()
      this.persist()
    },
    async register(payload) {
      await authApi.register(payload)
      await this.login({ email: payload.email, password: payload.password })
    },
    async fetchMe() {
      this.user = await authApi.me()
      this.persist()
    },
    logout() {
      this.token = ''
      this.user = null
      this.persist()
    },
  },
})
