<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listProjects, deleteProject, uploadProject } from '@/api'

const router = useRouter()
const projects = ref([])
const uploading = ref(false)
const error = ref('')
const inputRef = ref(null)

async function load() {
  projects.value = await listProjects()
}

onMounted(load)

async function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  error.value = ''
  try {
    const p = await uploadProject(file)
    router.push(`/workspace/${p.id}`)
  } catch (err) {
    error.value = err.message
  } finally {
    uploading.value = false
    if (inputRef.value) inputRef.value.value = ''
  }
}

async function onDelete(id) {
  if (!confirm('确认删除该项目？')) return
  await deleteProject(id)
  await load()
}

function fmt(ts) {
  return new Date(ts).toLocaleString()
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="max-w-5xl mx-auto">
      <div class="flex items-center gap-4 mb-6">
        <h2 class="text-xl font-semibold">历史项目</h2>
        <label class="ml-auto btn-primary cursor-pointer">
          <input
            ref="inputRef"
            type="file"
            accept=".docx,.pdf"
            class="hidden"
            @change="onFile"
          />
          {{ uploading ? '上传解析中…' : '+ 新建翻译' }}
        </label>
      </div>
      <div v-if="error" class="mb-4 text-sm text-red-600">{{ error }}</div>

      <div v-if="!projects.length" class="text-gray-500 text-sm">
        还没有项目，点击右上角上传一份 .docx / .pdf 开始。
      </div>

      <div v-else class="bg-white rounded-lg border divide-y">
        <div
          v-for="p in projects"
          :key="p.id"
          class="flex items-center gap-4 px-4 py-3 hover:bg-gray-50"
        >
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">{{ p.name }}</div>
            <div class="text-xs text-gray-500 mt-0.5">
              {{ p.source_type?.toUpperCase() }} · 创建 {{ fmt(p.created_at) }}
              · 模型 {{ p.llm_provider }}/{{ p.llm_model }}
            </div>
          </div>
          <span class="text-xs text-gray-500">{{ p.status }}</span>
          <button class="btn-link" @click="router.push(`/workspace/${p.id}`)">打开</button>
          <button class="btn-link text-red-600" @click="onDelete(p.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.btn-primary {
  @apply px-4 py-1.5 rounded bg-brand-500 hover:bg-brand-600 text-white text-sm;
}
.btn-link {
  @apply text-sm text-brand-600 hover:underline;
}
</style>
