<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <RouterLink to="/admin" class="admin-brand" exact-active-class="active">
        <span class="brand-paw">🐾</span>
        <span>
          <strong>汪星图鉴</strong>
          <small>管理端</small>
        </span>
      </RouterLink>

      <nav class="admin-nav">
        <RouterLink to="/admin" exact-active-class="active">📊 数据概览</RouterLink>
        <RouterLink to="/admin/users" active-class="active">👥 用户管理</RouterLink>
        <RouterLink to="/admin/records" active-class="active">🖼️ 识别记录</RouterLink>
        <RouterLink to="/admin/breeds" active-class="active">📚 科普内容</RouterLink>
      </nav>

      <RouterLink to="/" class="btn btn-ghost btn-sm admin-back">← 返回前台</RouterLink>
    </aside>

    <div class="admin-content">
      <header class="admin-topbar">
        <div>
          <strong>你好，{{ auth.user?.nickname || auth.user?.username || '管理员' }}</strong>
          <span class="muted">今天也要照顾好每一只毛孩子～</span>
        </div>
        <button class="btn btn-ghost btn-sm" type="button" @click="logout">退出登录</button>
      </header>

      <main class="admin-main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()

function logout() {
  auth.logout()
  toast.success('已退出管理端')
  router.push('/login')
}
</script>