<script setup>
import { ref, nextTick } from 'vue'
import { askQA } from '@/api'
import { renderAnswerWithCitations } from '@/utils/markdown'

const props = defineProps({
  projectId: { type: String, required: true }
})
const emit = defineEmits(['jump'])

const messages = ref([]) // {role, html, citations}
const input = ref('')
const loading = ref(false)
const scrollEl = ref(null)

async function send() {
  const q = input.value.trim()
  if (!q || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', html: escape(q), citations: [] })
  loading.value = true
  await nextTick()
  scroll()
  try {
    const res = await askQA(props.projectId, q)
    messages.value.push({
      role: 'assistant',
      html: renderAnswerWithCitations(res.answer, res.citations),
      citations: res.citations
    })
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      html: `<span class="text-red-600">出错：${escape(e.message)}</span>`,
      citations: []
    })
  } finally {
    loading.value = false
    await nextTick()
    scroll()
  }
}

function scroll() {
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}
function escape(s) {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))
}

function onClickAnswer(e) {
  const a = e.target.closest('a[data-cite]')
  if (!a) return
  e.preventDefault()
  emit('jump', a.getAttribute('data-cite'))
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div
      ref="scrollEl"
      class="flex-1 overflow-y-auto scrollbar-thin px-3 py-3 space-y-3 text-sm"
      @click="onClickAnswer"
    >
      <div v-if="!messages.length" class="text-gray-400 text-xs">
        问问关于合同的任何问题，回答将带有条款引用。
      </div>
      <div v-for="(m, i) in messages" :key="i" class="flex">
        <div
          class="max-w-[95%] rounded-lg px-3 py-2"
          :class="
            m.role === 'user'
              ? 'ml-auto bg-brand-500 text-white'
              : 'bg-gray-100 text-gray-800'
          "
        >
          <div
            :class="m.role === 'assistant' ? 'md-body' : ''"
            v-html="m.html"
          ></div>
        </div>
      </div>
      <div v-if="loading" class="text-xs text-gray-500">思考中…</div>
    </div>
    <div class="border-t p-2 flex gap-2">
      <input
        v-model="input"
        @keydown.enter="send"
        placeholder="就合同提问…"
        class="flex-1 border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
      <button
        class="px-3 py-1.5 rounded bg-brand-500 hover:bg-brand-600 text-white text-sm disabled:opacity-50"
        :disabled="loading"
        @click="send"
      >
        发送
      </button>
    </div>
  </div>
</template>
