import http from './http'

export const authApi = {
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data),
  me: () => http.get('/auth/me')
}

export const breedApi = {
  list: (params = {}) => http.get('/breeds', { params }),
  get: (id) => http.get(`/breeds/${id}`),
  bySlug: (slug) => http.get(`/breeds/by-slug/${slug}`)
}

export const recognitionApi = {
  info: () => http.get('/recognition/info'),
  predict: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/recognition/predict', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const historyApi = {
  list: () => http.get('/history'),
  remove: (id) => http.delete(`/history/${id}`)
}

export const adminApi = {
  overview: () => http.get('/admin/overview'),
  users: () => http.get('/admin/users'),
  updateUser: (id, data) => http.patch(`/admin/users/${id}`, data),
  records: () => http.get('/admin/records'),
  removeRecord: (id) => http.delete(`/admin/records/${id}`),
  createBreed: (data) => http.post('/admin/breeds', data),
  updateBreed: (id, data) => http.put(`/admin/breeds/${id}`, data),
  deleteBreed: (id) => http.delete(`/admin/breeds/${id}`)
}