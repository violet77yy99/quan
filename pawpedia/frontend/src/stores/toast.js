import { defineStore } from 'pinia'

let seq = 0

export const useToastStore = defineStore('toast', {
  state: () => ({ items: [] }),
  actions: {
    push(message, type = 'info', timeout = 2800) {
      const id = ++seq
      this.items.push({ id, message, type })
      setTimeout(() => this.remove(id), timeout)
    },
    success(message) {
      this.push(message, 'success')
    },
    error(message) {
      this.push(message, 'error', 3600)
    },
    remove(id) {
      this.items = this.items.filter((item) => item.id !== id)
    }
  }
})