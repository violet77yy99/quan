import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

export const ASSET_BASE = API_BASE.startsWith('http')
  ? API_BASE.replace(/\/api\/?$/, '')
  : ''

const http = axios.create({
  baseURL: API_BASE,
  timeout: 60000
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('pawpedia_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('pawpedia_token')
      localStorage.removeItem('pawpedia_user')
    }
    return Promise.reject(error)
  }
)

export function assetUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${ASSET_BASE}${path}`
}

export default http