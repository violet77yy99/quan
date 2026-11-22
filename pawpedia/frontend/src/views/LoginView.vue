<template>
  <div class="page container auth-page">
    <div class="auth-card card">
      <div class="auth-art">
        <div class="auth-emoji">🐶</div>
        <h2>欢迎回来</h2>
        <p>登录后可以保存识别记录，也能进入管理端。</p>
        <div class="auth-paw-row">🐾 🐾 🐾</div>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <span class="eyebrow">Login</span>
        <h1>登录汪星图鉴</h1>

        <label class="field">
          <span>用户名</span>
          <input v-model.trim="form.username" type="text" placeholder="请输入用户名" autocomplete="username" />
        </label>
        <label class="field">
          <span>密码</span>
          <input v-model="form.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>

        <button class="btn btn-primary btn-block" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>

        <div class="demo-accounts">
          <span>演示账号：</span>
          <button type="button" class="link-btn" @click="fill('admin', 'admin123')">管理员</button>
          <button type="button" class="link-btn" @click="fill('user', 'user123456')">普通用户</button>
        </div>

        <p class="auth-switch">
          还没有账号？<RouterLink to="/register">去注册</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

function fill(username, password) {
  form.username = username
  form.password = password
}

async function submit() {
  if (!form.username || !form.password) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const user = await auth.login({ ...form })
    toast.success(`欢迎回来，${user.nickname || user.username}！`)
    router.push(route.query.redirect || '/')
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查账号密码'
  } finally {
    loading.value = false
  }
}
</script>