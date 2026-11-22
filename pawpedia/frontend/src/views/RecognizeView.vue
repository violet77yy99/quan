<template>
  <div class="page container recognize-page">
    <header class="page-head center">
      <span class="eyebrow">Recognize</span>
      <h1>这是哪位毛孩子？</h1>
      <p>上传一张清晰的狗狗照片，汪星图鉴来帮你认一认。</p>
    </header>

    <div class="recognize-grid">
      <section class="card upload-card">
        <div
          class="dropzone"
          :class="{ 'has-file': previewUrl }"
          @dragover.prevent
          @drop.prevent="handleDrop"
          @click="pickFile"
        >
          <img v-if="previewUrl" :src="previewUrl" alt="预览" class="preview" />
          <div v-else class="dropzone-empty">
            <div class="drop-icon">🐶</div>
            <h3>拖一张狗狗照片到这里</h3>
            <p>或者点击选择图片 · JPG / PNG · 不超过 8MB</p>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            hidden
            @change="onFileChange"
          />
        </div>

        <div class="upload-actions">
          <button class="btn btn-primary" type="button" :disabled="!file || loading" @click="predict">
            {{ loading ? '识别中…' : '开始识别' }}
          </button>
          <button class="btn btn-ghost" type="button" @click="reset">换一张</button>
        </div>
        <p class="hint">
          🔒 游客也可以识别；登录后会自动保存到「我的记录」。
        </p>
      </section>

      <section class="card result-card">
        <div v-if="!result" class="result-empty">
          <div class="result-empty-icon">🐾</div>
          <h3>识别结果会出现在这里</h3>
          <p>先选一张照片，再点「开始识别」。</p>
        </div>

        <div v-else class="result-body">
          <span class="result-badge">识别结果</span>
          <h2>{{ result.prediction.name_cn }}</h2>
          <ConfidenceBar :value="result.prediction.confidence" />

          <div class="top3">
            <div v-for="(item, index) in result.prediction.top3" :key="item.name_cn" class="top3-row">
              <span class="top3-rank">{{ index + 1 }}</span>
              <span class="top3-name">{{ item.name_cn }}</span>
              <span class="top3-value">{{ (item.confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>

          <div v-if="result.breed" class="breed-brief">
            <img :src="assetUrl(result.breed.image_url)" :alt="result.breed.name_cn" />
            <div>
              <h4>{{ result.breed.name_cn }} · {{ result.breed.name_en }}</h4>
              <p>{{ result.breed.intro }}</p>
              <div class="tag-row">
                <span class="tag">{{ result.breed.size_category }}</span>
                <span class="tag">{{ result.breed.difficulty }}</span>
                <span class="tag">{{ result.breed.origin }}</span>
              </div>
            </div>
          </div>

          <div class="result-actions">
            <RouterLink
              v-if="result.breed"
              :to="`/breed/${result.breed.slug}`"
              class="btn btn-primary"
            >
              查看完整科普
            </RouterLink>
            <RouterLink v-if="!auth.isLoggedIn" to="/login" class="btn btn-ghost">
              登录保存记录
            </RouterLink>
            <span v-else-if="result.saved" class="saved-note">✅ 已保存到历史记录</span>
          </div>
        </div>
      </section>
    </div>

    <section class="tips card">
      <h3>📸 拍得更好认的小建议</h3>
      <div class="tips-grid">
        <span>光线充足，避免逆光</span>
        <span>狗狗占画面主体</span>
        <span>尽量露出正脸和全身</span>
        <span>避免模糊、拼图和带大段文字的图片</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onUnmounted, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { assetUrl } from '../api/http'
import { recognitionApi } from '../api'
import ConfidenceBar from '../components/ConfidenceBar.vue'

const auth = useAuthStore()
const toast = useToastStore()

const fileInput = ref(null)
const file = ref(null)
const previewUrl = ref('')
const result = ref(null)
const loading = ref(false)

function pickFile() {
  fileInput.value?.click()
}

function setFile(nextFile) {
  if (!nextFile) return
  if (!nextFile.type.startsWith('image/')) {
    toast.error('请选择图片文件')
    return
  }
  if (nextFile.size > 8 * 1024 * 1024) {
    toast.error('图片不能超过 8MB')
    return
  }
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = nextFile
  previewUrl.value = URL.createObjectURL(nextFile)
  result.value = null
}

function onFileChange(event) {
  setFile(event.target.files?.[0])
  event.target.value = ''
}

function handleDrop(event) {
  setFile(event.dataTransfer.files?.[0])
}

async function predict() {
  if (!file.value || loading.value) return
  loading.value = true
  try {
    const { data } = await recognitionApi.predict(file.value)
    result.value = data
    toast.success(`识别完成：${data.prediction.name_cn}`)
  } catch (error) {
    const message = error.response?.data?.detail || '识别失败，请换一张图片再试'
    toast.error(message)
  } finally {
    loading.value = false
  }
}

function reset() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = null
  previewUrl.value = ''
  result.value = null
}

onUnmounted(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>