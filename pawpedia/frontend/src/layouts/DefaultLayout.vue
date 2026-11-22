<template>
  <div class="app-shell">
    <div class="bg-blob blob-one"></div>
    <div class="bg-blob blob-two"></div>
    <AppHeader />
    <main class="main">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'
import AppFooter from '../components/AppFooter.vue'
</script>