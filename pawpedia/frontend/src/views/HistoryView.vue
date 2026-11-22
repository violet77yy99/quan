<template>
  <div class="page container history-page">
    <header class="page-head">
      <span class="eyebrow">My Records</span>
      <h1>我的识别记录</h1>
      <p>每一次相遇，都值得被记住。</p>
    </header>

    <div class="stat-row">
      <div class="stat-card card"><span>总记录</span><strong>{{ records.length }}</strong></div>
      <div class="stat-card card"><span>平均置信度</span><strong>{{ avgConfidence }}%</strong></div>
      <div class="stat-card card"><span>最近一次</span><strong>{{ records.length ? formatDate(records[0].created_at) : '—' }}</strong></div>
    </div>

    <div v-if="loading" class="empty-state card"><div>🐾</div><h3>正在找记录…</h3></div>

    <div v-else-if="!records.length" class="empty-state card">
      <div>📷</div>
      <h3>还没有识别记录</h3>
      <p>去识别一只毛孩子，记录就会出现在这里。</p>
      <RouterLink to="/recognize" class="btn btn-primary">去识别</RouterLink>
    </div>

    <div v-else class="history-grid">
      <article v-for="record in records" :key="record.id" class="history-card card">
        <div class="history-thumb">
          <img :src="assetUrl(record.image_url)" :alt="record.predicted_name" loading="lazy" />
        </div>
        <div class="history-body">
          <div class="history-title">
            <h3>{{ record.predicted_name }}</h3>
            <button class="icon-btn danger" type="button" title="删除" @click="remove(record)">
              🗑️
            </button>
          </div>
          <ConfidenceBar :value="record.confidence" label="当次置信度" />
          <div class="history-meta">
            <span>{{ formatDate(record.created_at) }}</span>
            <span v-if="record.top3?.length">Top-3：{{ record.top3.map((i) => i.name_cn).join(' / ') }}</span>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useToastStore } from '../stores/toast'
import { historyApi } from '../api'
import { assetUrl } from '../api/http'
import ConfidenceBar from '../components/ConfidenceBar.vue'

const toast = useToastStore()
const records = ref([])
const loading = ref(false)

const avgConfidence = computed(() => {
  if (!records.value.length) return 0
  const sum = records.value.reduce((acc, item) => acc + item.confidence, 0)
  return ((sum / records.value.length) * 100).toFixed(1)
})

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value.endsWith('Z') ? value : `${value}Z`)
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function load() {
  loading.value = true
  try {
    const { data } = await historyApi.list()
    records.value = data
  } catch {
    toast.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

async function remove(record) {
  if (!window.confirm(`确定删除「${record.predicted_name}」这条记录吗？`)) return
  try {
    await historyApi.remove(record.id)
    records.value = records.value.filter((item) => item.id !== record.id)
    toast.success('已删除')
  } catch {
    toast.error('删除失败，请稍后再试')
  }
}

onMounted(load)
</script>