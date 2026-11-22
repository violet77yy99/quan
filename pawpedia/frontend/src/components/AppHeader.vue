<template>
  <header class="site-header">
    <div class="container header-inner">
      <RouterLink to="/" class="brand" @click="menuOpen = false">
        <span class="brand-paw">🐾</span>
        <span class="brand-text">
          <strong>汪星图鉴</strong>
          <small>PawPedia</small>
        </span>
      </RouterLink>

      <nav class="nav" :class="{ open: menuOpen }">
        <RouterLink to="/" @click="menuOpen = false">首页</RouterLink>
        <RouterLink to="/recognize" @click="menuOpen = false">图片识别</RouterLink>
        <RouterLink to="/encyclopedia" @click="menuOpen = false">犬类图鉴</RouterLink>
        <RouterLink v-if="auth.isLoggedIn" to="/history" @click="menuOpen = false">
          我的记录
        </RouterLink>
      </nav>

      <div class="header-actions">
        <template v-if="auth.isLoggedIn">
          <RouterLink v-if="auth.isAdmin" to="/admin" class="btn btn-ghost btn-sm">
            管理端
          </RouterLink>
          <span class="user-chip">🐶 {{ auth.user?.nickname || auth.user?.username }}</span>
          <button class="btn btn-ghost btn-sm" type="button" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-ghost btn-sm">登录</RouterLink>
          <RouterLink to="/register" class="btn btn-primary btn-sm">注册</RouterLink>
        </template>
        <button class="menu-toggle" type="button" @click="menuOpen = !menuOpen">☰</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()
const menuOpen = ref(false)

function logout() {
  auth.logout()
  toast.success('已退出登录，欢迎再来玩～')
  router.push('/')
}
</script>