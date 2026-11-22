<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-mask" @click.self="$emit('update:modelValue', false)">
        <div class="modal-card" :style="{ maxWidth: width }">
          <div class="modal-head">
            <h3>{{ title }}</h3>
            <button class="icon-btn" type="button" @click="$emit('update:modelValue', false)">
              ✕
            </button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-foot">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  width: { type: String, default: '640px' }
})
defineEmits(['update:modelValue'])
</script>