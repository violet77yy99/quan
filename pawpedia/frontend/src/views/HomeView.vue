<template>
  <div class="page home-page">
    <section class="hero container">
      <div class="hero-copy">
        <span class="eyebrow">🐾 AI 犬类识别 · PawPedia</span>
        <h1>认识每一只<br /><em>毛孩子</em></h1>
        <p class="hero-sub">
          上传一张照片，几秒钟告诉你它是什么品种，再送你一张专属科普卡片。
          比格、柯基、金毛、边牧……还有一只乱入的橘猫。
        </p>
        <div class="hero-actions">
          <RouterLink to="/recognize" class="btn btn-primary btn-lg">开始识别 →</RouterLink>
          <RouterLink to="/encyclopedia" class="btn btn-ghost btn-lg">逛逛图鉴</RouterLink>
        </div>
        <div class="hero-stats">
          <div><strong>{{ breeds.length || 8 }}</strong><span>个品种</span></div>
          <div><strong>{{ modelInfo?.num_classes || 8 }}</strong><span>类识别</span></div>
          <div><strong>24h</strong><span>随时在线</span></div>
        </div>
      </div>

      <div class="hero-collage">
        <div class="hero-photo photo-a">
          <img :src="assetUrl('/static/breeds/samoyed.jpg')" alt="萨摩耶" />
        </div>
        <div class="hero-photo photo-b">
          <img :src="assetUrl('/static/breeds/corgi.jpg')" alt="柯基" />
        </div>
        <div class="hero-photo photo-c">
          <img :src="assetUrl('/static/breeds/golden-retriever.jpg')" alt="金毛" />
        </div>
        <div class="floating-card">
          <span>✨ 已收录</span>
          <strong>{{ breeds.length || 8 }} 个毛孩子</strong>
        </div>
      </div>
    </section>

    <section class="section container">
      <div class="section-head">
        <div>
          <span class="eyebrow">Features</span>
          <h2>不只是识别，更是一本会说话的图鉴</h2>
        </div>
      </div>
      <div class="feature-grid">
        <div class="feature-card card">
          <span class="feature-icon">📷</span>
          <h3>拍一张，认出来</h3>
          <p>上传狗狗照片，返回品种名称、置信度和 Top-3 候选。</p>
        </div>
        <div class="feature-card card">
          <span class="feature-icon">📚</span>
          <h3>边看边学</h3>
          <p>中英文名、性格、体型、饲养难度、原产地和市场价格，一张卡片全都有。</p>
        </div>
        <div class="feature-card card">
          <span class="feature-icon">🕘</span>
          <h3>记录每一次相遇</h3>
          <p>登录后自动保存识别历史，随时回看、随时删除。</p>
        </div>
      </div>
    </section>

    <section class="section container">
      <div class="section-head">
        <div>
          <span class="eyebrow">Popular</span>
          <h2>热门品种</h2>
        </div>
        <RouterLink to="/encyclopedia" class="text-link">查看全部 →</RouterLink>
      </div>
      <div class="breed-grid">
        <BreedCard v-for="breed in featured" :key="breed.id" :breed="breed" />
      </div>
    </section>

    <section class="section container">
      <div class="how-card card">
        <div class="how-copy">
          <span class="eyebrow">How it works</span>
          <h2>三步，认识新朋友</h2>
          <ol class="steps">
            <li><span>1</span><div><strong>上传照片</strong><p>拖拽或点击选择一张清晰的狗狗照片。</p></div></li>
            <li><span>2</span><div><strong>AI 识别</strong><p>模型给出品种、置信度和候选列表。</p></div></li>
            <li><span>3</span><div><strong>看科普</strong><p>顺手把性格、体型、价格都了解一遍。</p></div></li>
          </ol>
        </div>
        <div class="how-art">
          <div class="how-emoji">🐕‍🦺</div>
          <div class="how-bubble">“今天也要认识新朋友呀～”</div>
        </div>
      </div>
    </section>

    <section class="cta-band container">
      <div>
        <span class="eyebrow">Ready?</span>
        <h2>上传一张照片，听听它是什么品种</h2>
        <p>游客也能直接识别；登录后自动保存记录。</p>
      </div>
      <RouterLink to="/recognize" class="btn btn-primary btn-lg">立即识别 →</RouterLink>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import BreedCard from '../components/BreedCard.vue'
import { breedApi, recognitionApi } from '../api'
import { assetUrl } from '../api/http'

const breeds = ref([])
const modelInfo = ref(null)

const featured = computed(() => breeds.value.slice(0, 4))

onMounted(async () => {
  try {
    const { data } = await breedApi.list()
    breeds.value = data
  } catch {
    breeds.value = []
  }
  try {
    const { data } = await recognitionApi.info()
    modelInfo.value = data
  } catch {
    modelInfo.value = null
  }
})
</script>