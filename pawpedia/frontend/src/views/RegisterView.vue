<template>
  <div class="page container auth-page">
    <div class="auth-card card">
      <div class="auth-art mint">
        <div class="auth-emoji">🐕</div>
        <h2>加入汪星</h2>
        <p>注册一个账号，开始收藏你和毛孩子的每一次相遇。</p>
        <div class="auth-paw-row">🐾 🐾 🐾</div>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <span class="eyebrow">Register</span>
        <h1>创建新账号</h1>

        <label class="field">
          <span>用户名</span>
          <input v-model.trim="form.username" type="text" placeholder="3-30 个字符" autocomplete="username" />
        </label>
        <label class="field">
          <span>昵称（可选）</span>
          <input v-model.trim="form.nickname" type="text" placeholder="想让大家怎么称呼你？" />
        </label>
        <label class="field">
          <span>密码</span>
          <input v-model="form.password" type="password" placeholder="至少 6 位" autocomplete="new-password" />
        </label>
        <label class="field">
          <span>确认密码</span>
          <input v-model="form.confirm" type="password" placeholder="再输入一次密码" autocomplete="new-password" />
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>

        <button class="btn btn-primary btn-block" type="submit" :disabled="loading">
          {{ loading ? '注册中…' : '注册并登录' }}
        </button>

        <p class="auth-switch">
          已经有账号？<RouterLink to="/login">去登录</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()

const form = reactive({ username: '', nickname: '', password: '', confirm: '' })
const loading = ref(false)
const error = ref('')

async function submit() {
  if (form.username.length < 3) {
    error.value = '用户名至少 3 个字符'
    return
  }
  if (form.password.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  if (form.password !== form.confirm) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const user = await auth.register({
      username: form.username,
      password: form.password,
      nickname: form.nickname || form.username
    })
    toast.success(`注册成功，欢迎 ${user.nickname || user.username}！`)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || '注册失败，请稍后再试'
  } finally {
    loading.value = false
  }
}
</script>