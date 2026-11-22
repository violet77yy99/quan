<template>
  <div class="toast-host">
    <TransitionGroup name="toast">
      <div v-for="item in toast.items" :key="item.id" class="toast" :class="item.type">
        <span>{{ icon(item.type) }}</span>
        <span>{{ item.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useToastStore } from '../stores/toast'

const toast = useToastStore()

function icon(type) {
  if (type === 'success') return '✅'
  if (type === 'error') return '⚠️'
  return '🐾'
}
</script>