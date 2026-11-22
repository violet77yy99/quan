<template>
  <div class="admin-page">
    <header class="page-head admin-head-row">
      <div>
        <span class="eyebrow">Breeds</span>
        <h1>科普内容</h1>
        <p>维护图鉴里的犬种卡片。</p>
      </div>
      <button class="btn btn-primary" type="button" @click="openCreate">＋ 新增品种</button>
    </header>

    <section class="card">
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>图片</th><th>中文名</th><th>英文名</th><th>体型</th><th>难度</th><th>价格</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="breed in breeds" :key="breed.id">
              <td><img class="thumb" :src="assetUrl(breed.image_url)" :alt="breed.name_cn" /></td>
              <td><strong>{{ breed.name_cn }}</strong><span v-if="!breed.is_dog" class="self-tag">非犬类</span></td>
              <td>{{ breed.name_en }}</td>
              <td>{{ breed.size_category }}</td>
              <td>{{ breed.difficulty }}</td>
              <td>{{ breed.market_price }}</td>
              <td class="table-actions">
                <button class="btn btn-ghost btn-sm" type="button" @click="openEdit(breed)">编辑</button>
                <button class="btn btn-danger btn-sm" type="button" @click="remove(breed)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <ModalDialog v-model="modalOpen" :title="editingId ? '编辑科普内容' : '新增科普内容'">
      <form class="breed-form" @submit.prevent="save">
        <div class="form-grid">
          <label class="field"><span>slug（英文标识）</span><input v-model.trim="form.slug" required placeholder="corgi" /></label>
          <label class="field"><span>中文名</span><input v-model.trim="form.name_cn" required placeholder="柯基" /></label>
          <label class="field"><span>英文名</span><input v-model.trim="form.name_en" placeholder="Welsh Corgi" /></label>
          <label class="field"><span>体型</span>
            <select v-model="form.size_category" class="select">
              <option>小型犬</option><option>中型犬</option><option>大型犬</option><option>其他</option>
            </select>
          </label>
          <label class="field"><span>饲养难度</span>
            <select v-model="form.difficulty" class="select">
              <option>容易</option><option>中等</option><option>较难</option>
            </select>
          </label>
          <label class="field"><span>原产地</span><input v-model.trim="form.origin" placeholder="英国威尔士" /></label>
          <label class="field"><span>参考价格</span><input v-model.trim="form.market_price" placeholder="1500 - 6000 元" /></label>
          <label class="field"><span>图片地址</span><input v-model.trim="form.image_url" placeholder="/static/breeds/corgi.jpg" /></label>
        </div>
        <label class="field"><span>性格关键词（逗号分隔）</span><input v-model.trim="form.personality" placeholder="活泼,勇敢,聪明" /></label>
        <label class="field"><span>简介</span><textarea v-model.trim="form.intro" rows="4" placeholder="写一段这个品种的介绍…"></textarea></label>
        <label class="check-row"><input v-model="form.is_dog" type="checkbox" /> 这是犬类（取消勾选表示干扰项）</label>
      </form>

      <template #footer>
        <button class="btn btn-ghost" type="button" @click="modalOpen = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import ModalDialog from '../../components/ModalDialog.vue'
import { adminApi, breedApi } from '../../api'
import { assetUrl } from '../../api/http'
import { useToastStore } from '../../stores/toast'

const toast = useToastStore()
const breeds = ref([])
const modalOpen = ref(false)
const editingId = ref(null)
const saving = ref(false)

function emptyForm() {
  return {
    slug: '',
    name_cn: '',
    name_en: '',
    intro: '',
    personality: '',
    size_category: '中型犬',
    difficulty: '中等',
    origin: '',
    market_price: '',
    image_url: '',
    is_dog: true
  }
}

const form = reactive(emptyForm())

async function reloadBreeds() {
  const { data } = await breedApi.list()
  breeds.value = data
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  modalOpen.value = true
}

function openEdit(breed) {
  editingId.value = breed.id
  Object.assign(form, emptyForm(), {
    slug: breed.slug,
    name_cn: breed.name_cn,
    name_en: breed.name_en,
    intro: breed.intro,
    personality: breed.personality,
    size_category: breed.size_category,
    difficulty: breed.difficulty,
    origin: breed.origin,
    market_price: breed.market_price,
    image_url: breed.image_url,
    is_dog: breed.is_dog
  })
  modalOpen.value = true
}

async function save() {
  if (!form.slug || !form.name_cn) {
    toast.error('slug 和中文名必填')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await adminApi.updateBreed(editingId.value, { ...form })
      toast.success('已更新')
    } else {
      await adminApi.createBreed({ ...form })
      toast.success('已新增')
    }
    modalOpen.value = false
    await reloadBreeds()
  } catch (error) {
    toast.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(breed) {
  if (!window.confirm(`确定删除「${breed.name_cn}」的科普内容吗？`)) return
  try {
    await adminApi.deleteBreed(breed.id)
    breeds.value = breeds.value.filter((item) => item.id !== breed.id)
    toast.success('已删除')
  } catch {
    toast.error('删除失败')
  }
}

onMounted(reloadBreeds)
</script>