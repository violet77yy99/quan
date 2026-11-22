<template>
  <div class="admin-page">
    <header class="page-head">
      <span class="eyebrow">Records</span>
      <h1>识别记录</h1>
      <p>查看所有用户的识别结果，必要时可以删除。</p>
    </header>

    <section class="card">
      <div class="card-head">
        <h2>全部记录</h2>
        <span class="muted">最近 {{ records.length }} 条</span>
      </div>

      <div v-if="!records.length" class="empty-state inner">
        <div>🐾</div>
        <h3>还没有识别记录</h3>
      </div>

      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>图片</th><th>用户</th><th>识别结果</th><th>置信度</th><th>Top-3</th><th>时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id">
              <td><img class="thumb" :src="assetUrl(record.image_url)" :alt="record.predicted_name" /></td>
              <td>{{ record.nickname || record.username || '游客' }}</td>
              <td><strong>{{ record.predicted_name }}</strong></td>
              <td>{{ (record.confidence * 100).toFixed(1) }}%</td>
              <td class="muted">{{ (record.top3 || []).map((i) => i.name_cn).join(' / ') }}</td>
              <td class="muted">{{ formatDate(record.created_at) }}</td>
              <td>
                <button class="btn btn-danger btn-sm" type="button" @click="remove(record)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { adminApi } from '../../api'
import { assetUrl } from '../../api/http'
import { useToastStore } from '../../stores/toast'

const toast = useToastStore()
const records = ref([])

function formatDate(value) {
  if (!value) return '—'
  return new Date(value.endsWith('Z') ? value : `${value}Z`).toLocaleString('zh-CN', {
    hour12: false
  })
}

async function load() {
  const { data } = await adminApi.records()
  records.value = data
}

async function remove(record) {
  if (!window.confirm(`确定删除 ${record.predicted_name} 的这条记录吗？`)) return
  try {
    await adminApi.removeRecord(record.id)
    records.value = records.value.filter((item) => item.id !== record.id)
    toast.success('已删除')
  } catch {
    toast.error('删除失败')
  }
}

onMounted(load)
</script>