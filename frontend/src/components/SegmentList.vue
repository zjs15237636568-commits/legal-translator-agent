<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps({
  segments: { type: Array, required: true },
  side: { type: String, required: true } // 'original' | 'translation'
})

const rows = computed(() =>
  props.segments.map((s) => ({
    id: s.id,
    status: s.status,
    error: s.error,
    clauseNo: s.clause_no,
    seq: s.seq,
    heading: s.heading,
    html:
      props.side === 'original'
        ? renderMarkdown(s.original_md)
        : renderMarkdown(s.translated_md || '')
  }))
)

const emit = defineEmits(['retry'])
</script>

<template>
  <div v-for="r in rows" :key="r.id" :data-anchor-id="r.id" class="segment-anchor">
    <!-- 状态徽标（仅 translation 栏） -->
    <div v-if="side === 'translation'" class="flex items-center gap-2 text-xs mb-1">
      <span v-if="r.status === 'streaming'" class="text-blue-600">
        <span class="inline-block w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse mr-1"></span>
        正在翻译…
      </span>
      <span v-else-if="r.status === 'done'" class="text-emerald-600">✓ 完成</span>
      <span v-else-if="r.status === 'failed'" class="text-red-600">
        ✗ 失败：{{ r.error }}
        <button class="ml-2 underline" @click="emit('retry', r.id)">重试</button>
      </span>
      <span v-else class="text-gray-400">待翻译</span>
    </div>

    <div v-if="r.html" class="md-body" v-html="r.html"></div>
    <div
      v-else-if="side === 'translation' && r.status === 'streaming'"
      class="text-gray-400 text-sm italic"
    >
      …
    </div>
    <div v-else-if="side === 'translation'" class="text-gray-300 text-sm italic">（待翻译）</div>
  </div>
</template>
