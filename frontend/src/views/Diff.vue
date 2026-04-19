<script setup>
import { onMounted, ref } from 'vue'
import { listProjects, diffProjects } from '@/api'

const projects = ref([])
const leftId = ref('')
const rightId = ref('')
const loading = ref(false)
const items = ref([])
const error = ref('')

onMounted(async () => {
  projects.value = await listProjects()
})

async function run() {
  error.value = ''
  items.value = []
  if (!leftId.value || !rightId.value || leftId.value === rightId.value) {
    error.value = '请选择两个不同的项目'
    return
  }
  loading.value = true
  try {
    const r = await diffProjects(leftId.value, rightId.value)
    items.value = r.items
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function typeLabel(t) {
  return { added: '新增', removed: '删除', modified: '修改', unchanged: '未变' }[t] || t
}
function typeClass(t) {
  return {
    added: 'border-emerald-300 bg-emerald-50 text-emerald-700',
    removed: 'border-red-300 bg-red-50 text-red-700',
    modified: 'border-amber-300 bg-amber-50 text-amber-800',
    unchanged: 'border-gray-200 bg-gray-50 text-gray-600'
  }[t]
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="max-w-5xl mx-auto">
      <h2 class="text-xl font-semibold mb-4">版本比对</h2>

      <div class="bg-white border rounded-lg p-4 flex items-end gap-3 mb-5">
        <div class="flex-1">
          <label class="block text-xs text-gray-500 mb-1">旧版（Left）</label>
          <select v-model="leftId" class="input">
            <option value="" disabled>选择项目</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="flex-1">
          <label class="block text-xs text-gray-500 mb-1">新版（Right）</label>
          <select v-model="rightId" class="input">
            <option value="" disabled>选择项目</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <button class="btn-primary" :disabled="loading" @click="run">
          {{ loading ? '比对中…' : '开始比对' }}
        </button>
      </div>

      <div v-if="error" class="text-red-600 text-sm mb-3">{{ error }}</div>

      <div v-if="!loading && items.length === 0" class="text-gray-400 text-sm">
        暂无比对结果。
      </div>

      <div class="space-y-3">
        <div
          v-for="(it, i) in items"
          :key="i"
          class="border rounded-lg p-3"
          :class="typeClass(it.type)"
        >
          <div class="flex items-center gap-2 text-sm font-medium mb-1">
            <span class="px-2 py-0.5 rounded text-xs bg-white/70">{{ typeLabel(it.type) }}</span>
            <span class="text-gray-600 text-xs">
              Left: {{ it.left_id || '—' }} / Right: {{ it.right_id || '—' }}
            </span>
          </div>
          <div class="text-sm text-gray-800">{{ it.summary_zh }}</div>
          <div v-if="it.business_impact_zh" class="text-sm text-gray-700 mt-1">
            <span class="font-medium">业务影响：</span>{{ it.business_impact_zh }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input {
  @apply w-full px-2 py-1.5 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm bg-white;
}
.btn-primary {
  @apply px-4 py-1.5 rounded bg-brand-500 hover:bg-brand-600 text-white text-sm disabled:opacity-50;
}
</style>
