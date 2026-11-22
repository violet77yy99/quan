<template>
  <div class="admin-page">
    <header class="page-head">
      <span class="eyebrow">Dashboard</span>
      <h1>数据概览</h1>
      <p>看看今天的汪星图鉴发生了什么。</p>
    </header>

    <div v-if="loading" class="empty-state card"><div>🐾</div><h3>加载中…</h3></div>

    <template v-else-if="overview">
      <div class="stat-row four">
        <div class="stat-card card"><span>总用户</span><strong>{{ overview.total_users }}</strong><em>👥</em></div>
        <div class="stat-card card"><span>总识别</span><strong>{{ overview.total_records }}</strong><em>🖼️</em></div>
        <div class="stat-card card"><span>科普内容</span><strong>{{ overview.total_breeds }}</strong><em>📚</em></div>
        <div class="stat-card card"><span>今日识别</span><strong>{{ overview.today_records }}</strong><em>✨</em></div>
      </div>

      <div class="admin-grid">
        <section class="card">
          <div class="card-head">
            <h2>最近识别</h2>
            <RouterLink to="/admin/records" class="text-link">查看全部 →</RouterLink>
          </div>
          <div v-if="overview.recent_records.length" class="table-wrap">
            <table class="table">
              <thead><tr><th>图片</th><th>用户</th><th>结果</th><th>置信度</th><th>时间</th></tr></thead>
              <tbody>
                <tr v-for="record in overview.recent_records" :key="record.id">
                  <td><img class="thumb" :src="assetUrl(record.image_url)" :alt="record.predicted_name" /></td>
                  <td>{{ record.nickname || record.username || '游客' }}</td>
                  <td><strong>{{ record.predicted_name }}</strong></td>
                  <td>{{ (record.confidence * 100).toFixed(1) }}%</td>
                  <td class="muted">{{ formatDate(record.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="muted">还没有识别记录。</p>
        </section>

        <section class="card">
          <div class="card-head"><h2>热门品种</h2></div>
          <div v-if="overview.top_breeds.length" class="rank-list">
            <div v-for="(item, index) in overview.top_breeds" :key="item.name" class="rank-item">
              <span class="rank-index">{{ index + 1 }}</span>
              <span class="rank-name">{{ item.name }}</span>
              <div class="rank-bar"><span :style="{ width: `${barWidth(item.count)}%` }"></span></div>
              <strong>{{ item.count }}</strong>
            </div>
          </div>
          <p v-else class="muted">还没有识别数据。</p>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { adminApi } from '../../api'
import { assetUrl } from '../../api/http'

const overview = ref(null)
const loading = ref(false)

const maxCount = computed(() => {
  const list = overview.value?.top_breeds || []
  return Math.max(1, ...list.map((item) => item.count))
})

function barWidth(count) {
  return Math.max(8, (count / maxCount.value) * 100)
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value.endsWith('Z') ? value : `${value}Z`).toLocaleString('zh-CN', {
    hour12: false
  })
}

async function load() {
  loading.value = true
  try {
    const { data } = await adminApi.overview()
    overview.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>