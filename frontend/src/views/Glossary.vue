<script setup>
import { onMounted, ref } from 'vue'
import { listGlossary, putGlossary } from '@/api'

const items = ref([])
const saving = ref(false)
const saved = ref('')

async function load() {
  const r = await listGlossary()
  items.value = r.items
}
onMounted(load)

function add() {
  items.value.push({ en: '', zh: '', note: '' })
}
function remove(i) {
  items.value.splice(i, 1)
}
async function save() {
  const clean = items.value
    .map((t) => ({
      en: (t.en || '').trim(),
      zh: (t.zh || '').trim(),
      note: (t.note || '').trim()
    }))
    .filter((t) => t.en && t.zh)
  saving.value = true
  try {
    const r = await putGlossary(clean)
    items.value = r.items
    saved.value = '已保存 ✓'
    setTimeout(() => (saved.value = ''), 1500)
  } finally {
    saving.value = false
  }
}
function download() {
  const blob = new Blob([JSON.stringify(items.value, null, 2)], {
    type: 'application/json'
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'glossary.json'
  a.click()
  URL.revokeObjectURL(url)
}
async function upload(e) {
  const f = e.target.files?.[0]
  if (!f) return
  const text = await f.text()
  try {
    const arr = JSON.parse(text)
    if (Array.isArray(arr)) items.value = arr
  } catch {
    alert('JSON 解析失败')
  }
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="max-w-4xl mx-auto">
      <div class="flex items-center gap-3 mb-4">
        <h2 class="text-xl font-semibold">术语库</h2>
        <span class="text-xs text-gray-500">
          仅用于专有名词强制翻译。匹配：整词、大小写不敏感。
        </span>
        <div class="ml-auto flex gap-2">
          <label class="btn-secondary cursor-pointer">
            导入 JSON
            <input type="file" accept="application/json" class="hidden" @change="upload" />
          </label>
          <button class="btn-secondary" @click="download">导出 JSON</button>
          <button class="btn-primary" :disabled="saving" @click="save">
            {{ saving ? '保存中…' : '保存' }}
          </button>
          <span v-if="saved" class="text-emerald-600 text-sm self-center">{{ saved }}</span>
        </div>
      </div>

      <div class="bg-white border rounded-lg overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="px-3 py-2 text-left w-1/4">English</th>
              <th class="px-3 py-2 text-left w-2/5">中文</th>
              <th class="px-3 py-2 text-left">备注</th>
              <th class="px-3 py-2 w-20"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(t, i) in items" :key="i" class="border-t">
              <td class="px-3 py-1.5">
                <input v-model="t.en" class="input" placeholder="e.g. Official Wallet" />
              </td>
              <td class="px-3 py-1.5">
                <input v-model="t.zh" class="input" placeholder="官方钱包（…）" />
              </td>
              <td class="px-3 py-1.5">
                <input v-model="t.note" class="input" placeholder="可选备注" />
              </td>
              <td class="px-3 py-1.5 text-right">
                <button class="text-red-500 text-xs" @click="remove(i)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="p-3 border-t">
          <button class="btn-secondary" @click="add">+ 新增一行</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input {
  @apply w-full px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-brand-500;
}
.btn-primary {
  @apply px-4 py-1.5 rounded bg-brand-500 hover:bg-brand-600 text-white text-sm disabled:opacity-50;
}
.btn-secondary {
  @apply px-3 py-1.5 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm;
}
</style>
