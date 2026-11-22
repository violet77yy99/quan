import { defineStore } from 'pinia'
import { authApi } from '../api'

function readUser() {
  try {
    return JSON.parse(localStorage.getItem('pawpedia_user') || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('pawpedia_token') || '',
    user: readUser()
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    isAdmin: (state) => state.user?.role === 'admin'
  },
  actions: {
    setSession(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('pawpedia_token', token)
      localStorage.setItem('pawpedia_user', JSON.stringify(user))
    },
    async login(payload) {
      const { data } = await authApi.login(payload)
      this.setSession(data.access_token, data.user)
      return data.user
    },
    async register(payload) {
      const { data } = await authApi.register(payload)
      this.setSession(data.access_token, data.user)
      return data.user
    },
    async fetchMe() {
      if (!this.token) return null
      try {
        const { data } = await authApi.me()
        this.user = data
        localStorage.setItem('pawpedia_user', JSON.stringify(data))
        return data
      } catch {
        this.logout()
        return null
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('pawpedia_token')
      localStorage.removeItem('pawpedia_user')
    }
  }
})