<template>
  <div class="confidence">
    <div class="confidence-head">
      <span>{{ label }}</span>
      <strong>{{ percent }}%</strong>
    </div>
    <div class="bar">
      <span :class="tone" :style="{ width: `${percent}%` }"></span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  label: { type: String, default: '置信度' }
})

const percent = computed(() => Math.round(Math.max(0, Math.min(1, props.value)) * 1000) / 10)
const tone = computed(() => {
  if (props.value >= 0.8) return 'good'
  if (props.value >= 0.6) return 'mid'
  return 'low'
})
</script>