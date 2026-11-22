<template>
  <div class="page container encyclopedia-page">
    <header class="page-head">
      <span class="eyebrow">Encyclopedia</span>
      <h1>犬类图鉴</h1>
      <p>按名字搜一搜，或者按体型筛一筛，找到你想认识的毛孩子。</p>
    </header>

    <div class="toolbar card">
      <div class="search-box">
        <span>🔍</span>
        <input
          v-model="search"
          type="search"
          placeholder="搜索品种名，例如：柯基、金毛、边牧…"
        />
      </div>
      <div class="filter-pills">
        <button
          v-for="item in sizes"
          :key="item"
          type="button"
          class="pill"
          :class="{ active: size === item }"
          @click="size = item"
        >
          {{ item }}
        </button>
      </div>
    </div>

    <div class="list-meta">
      <span>共 {{ breeds.length }} 个品种</span>
      <span v-if="loading">加载中…</span>
    </div>

    <div v-if="breeds.length" class="breed-grid">
      <BreedCard v-for="breed in breeds" :key="breed.id" :breed="breed" />
    </div>
    <div v-else-if="!loading" class="empty-state card">
      <div>🐾</div>
      <h3>没有找到这个品种</h3>
      <p>换个关键词，或者点「全部」看看。</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import BreedCard from '../components/BreedCard.vue'
import { breedApi } from '../api'

const breeds = ref([])
const search = ref('')
const size = ref('全部')
const loading = ref(false)
const sizes = ['全部', '小型犬', '中型犬', '大型犬', '其他']

let timer = null

async function load() {
  loading.value = true
  try {
    const { data } = await breedApi.list({
      search: search.value || undefined,
      size: size.value === '全部' ? undefined : size.value
    })
    breeds.value = data
  } catch {
    breeds.value = []
  } finally {
    loading.value = false
  }
}

watch([search, size], () => {
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})

onMounted(load)
</script>