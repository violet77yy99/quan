<template>
  <div class="admin-page">
    <header class="page-head">
      <span class="eyebrow">Users</span>
      <h1>用户管理</h1>
      <p>查看用户、调整角色、启用或禁用账号。</p>
    </header>

    <section class="card">
      <div class="card-head">
        <h2>用户列表</h2>
        <span class="muted">{{ users.length }} 位用户</span>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>ID</th><th>用户名</th><th>昵称</th><th>角色</th><th>状态</th><th>注册时间</th></tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.id }}</td>
              <td><strong>{{ user.username }}</strong><span v-if="user.id === auth.user?.id" class="self-tag">我</span></td>
              <td>{{ user.nickname || '—' }}</td>
              <td>
                <select
                  v-model="user.role"
                  class="select"
                  :disabled="user.id === auth.user?.id"
                  @change="changeRole(user)"
                >
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                </select>
              </td>
              <td>
                <label class="switch">
                  <input
                    v-model="user.is_active"
                    type="checkbox"
                    :disabled="user.id === auth.user?.id"
                    @change="toggleActive(user)"
                  />
                  <span></span>
                  {{ user.is_active ? '启用' : '禁用' }}
                </label>
              </td>
              <td class="muted">{{ formatDate(user.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { adminApi } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { useToastStore } from '../../stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const users = ref([])

function formatDate(value) {
  if (!value) return '—'
  return new Date(value.endsWith('Z') ? value : `${value}Z`).toLocaleString('zh-CN', {
    hour12: false
  })
}

async function load() {
  const { data } = await adminApi.users()
  users.value = data
}

async function changeRole(user) {
  try {
    await adminApi.updateUser(user.id, { role: user.role })
    toast.success('角色已更新')
  } catch (error) {
    toast.error(error.response?.data?.detail || '修改失败')
    await load()
  }
}

async function toggleActive(user) {
  try {
    await adminApi.updateUser(user.id, { is_active: user.is_active })
    toast.success(user.is_active ? '账号已启用' : '账号已禁用')
  } catch (error) {
    toast.error(error.response?.data?.detail || '修改失败')
    await load()
  }
}

onMounted(load)
</script>