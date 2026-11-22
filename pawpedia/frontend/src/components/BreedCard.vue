<template>
  <RouterLink :to="`/breed/${breed.slug}`" class="breed-card card">
    <div class="breed-thumb">
      <img :src="assetUrl(breed.image_url)" :alt="breed.name_cn" loading="lazy" />
      <span class="size-pill">{{ breed.size_category }}</span>
      <span v-if="!breed.is_dog" class="not-dog-pill">非犬类</span>
    </div>
    <div class="breed-body">
      <div class="breed-title">
        <h3>{{ breed.name_cn }}</h3>
        <span>{{ breed.name_en }}</span>
      </div>
      <p class="breed-intro">{{ breed.intro }}</p>
      <div class="breed-meta">
        <span>🌍 {{ breed.origin }}</span>
        <span>💪 {{ breed.difficulty }}</span>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
import { assetUrl } from '../api/http'

defineProps({
  breed: { type: Object, required: true }
})
</script>