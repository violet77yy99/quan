<template>
  <div class="page container breed-detail-page">
    <RouterLink to="/encyclopedia" class="back-link">← 返回犬类图鉴</RouterLink>

    <div v-if="loading" class="empty-state card">
      <div>🐾</div>
      <h3>正在翻开图鉴…</h3>
    </div>

    <div v-else-if="error" class="empty-state card">
      <div>😿</div>
      <h3>{{ error }}</h3>
      <RouterLink to="/encyclopedia" class="btn btn-primary">回到图鉴</RouterLink>
    </div>

    <article v-else-if="breed" class="breed-detail card">
      <div class="detail-photo">
        <img :src="assetUrl(breed.image_url)" :alt="breed.name_cn" />
        <span class="size-pill">{{ breed.size_category }}</span>
      </div>

      <div class="detail-info">
        <div class="detail-title">
          <div>
            <h1>{{ breed.name_cn }}</h1>
            <p class="detail-en">{{ breed.name_en }}</p>
          </div>
          <span v-if="!breed.is_dog" class="not-dog-pill">非犬类 · 干扰项</span>
        </div>

        <p class="detail-intro">{{ breed.intro }}</p>

        <div class="info-grid">
          <div><span>原产地</span><strong>{{ breed.origin || '—' }}</strong></div>
          <div><span>体型</span><strong>{{ breed.size_category }}</strong></div>
          <div><span>饲养难度</span><strong>{{ breed.difficulty }}</strong></div>
          <div><span>参考价格</span><strong>{{ breed.market_price || '—' }}</strong></div>
        </div>

        <div class="detail-block">
          <h3>性格关键词</h3>
          <div class="tag-row">
            <span v-for="tag in personalityTags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <RouterLink to="/recognize" class="btn btn-primary">识别我的狗狗</RouterLink>
          <RouterLink to="/encyclopedia" class="btn btn-ghost">继续逛图鉴</RouterLink>
        </div>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { breedApi } from '../api'
import { assetUrl } from '../api/http'

const route = useRoute()
const breed = ref(null)
const loading = ref(false)
const error = ref('')

const personalityTags = computed(() =>
  (breed.value?.personality || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
)

async function load(slug) {
  loading.value = true
  error.value = ''
  try {
    const { data } = await breedApi.bySlug(slug)
    breed.value = data
  } catch {
    breed.value = null
    error.value = '没有找到这个品种的科普卡片'
  } finally {
    loading.value = false
  }
}

onMounted(() => load(route.params.slug))
watch(() => route.params.slug, (slug) => slug && load(slug))
</script>