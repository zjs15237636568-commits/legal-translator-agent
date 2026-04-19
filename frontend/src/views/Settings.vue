<script setup>
import { onMounted, ref } from 'vue'
import { getConfig, updateConfig } from '@/api'

const cfg = ref(null)
const saving = ref(false)
const saved = ref('')

async function load() {
  cfg.value = await getConfig()
}
onMounted(load)

async function save() {
  saving.value = true
  try {
    cfg.value = await updateConfig(cfg.value)
    saved.value = '已保存 ✓'
    setTimeout(() => (saved.value = ''), 1500)
  } finally {
    saving.value = false
  }
}

const providerMeta = {
  openai: { label: 'OpenAI', hint: '官方 OpenAI API' },
  claude: { label: 'Claude (Anthropic)', hint: 'Anthropic 官方 API' },
  deepseek: { label: 'DeepSeek', hint: 'OpenAI 兼容协议' }
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="max-w-3xl mx-auto" v-if="cfg">
      <h2 class="text-xl font-semibold mb-4">模型配置</h2>
      <p class="text-sm text-gray-500 mb-4">
        API Key 以 AES-GCM 加密存储于本地 <code>data/config.enc</code>。文件内容不会落盘。
      </p>

      <div class="bg-white border rounded-lg p-4 mb-4">
        <label class="text-sm font-medium block mb-2">当前使用的供应商</label>
        <div class="flex gap-3">
          <label
            v-for="(meta, name) in providerMeta"
            :key="name"
            class="flex-1 border rounded-md px-3 py-2 cursor-pointer"
            :class="cfg.active_provider === name ? 'border-brand-500 bg-brand-50' : 'border-gray-200'"
          >
            <input type="radio" v-model="cfg.active_provider" :value="name" class="mr-2" />
            <span class="font-medium">{{ meta.label }}</span>
            <div class="text-xs text-gray-500">{{ meta.hint }}</div>
          </label>
        </div>
      </div>

      <div
        v-for="(meta, name) in providerMeta"
        :key="name"
        class="bg-white border rounded-lg p-4 mb-3"
      >
        <div class="font-medium mb-3">{{ meta.label }}</div>
        <div class="grid grid-cols-3 gap-3">
          <div class="col-span-2">
            <label class="lbl">API Key</label>
            <input
              v-model="cfg.providers[name].api_key"
              type="password"
              class="input"
              placeholder="sk-..."
            />
            <div class="text-xs text-gray-400 mt-1">
              已保存的 key 以掩码显示，修改时清空并粘贴新 key；保留掩码则使用旧 key。
            </div>
          </div>
          <div>
            <label class="lbl">Model</label>
            <input v-model="cfg.providers[name].model" class="input" />
          </div>
          <div class="col-span-3">
            <label class="lbl">Base URL</label>
            <input v-model="cfg.providers[name].base_url" class="input" />
          </div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
        <span v-if="saved" class="text-emerald-600 text-sm">{{ saved }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input {
  @apply w-full px-2 py-1.5 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm;
}
.lbl {
  @apply block text-xs text-gray-500 mb-1;
}
.btn-primary {
  @apply px-4 py-1.5 rounded bg-brand-500 hover:bg-brand-600 text-white text-sm disabled:opacity-50;
}
</style>
