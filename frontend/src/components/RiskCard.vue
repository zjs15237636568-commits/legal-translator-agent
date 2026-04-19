<script setup>
import { computed } from 'vue'

const props = defineProps({
  risk: { type: Object, required: true }
})
const emit = defineEmits(['jump'])

const color = computed(() =>
  props.risk.level === 'red'
    ? 'border-red-300 bg-red-50'
    : 'border-amber-300 bg-amber-50'
)
const dot = computed(() =>
  props.risk.level === 'red' ? 'bg-red-500' : 'bg-amber-500'
)
</script>

<template>
  <div class="border rounded-md p-3 text-sm shadow-sm" :class="color">
    <div class="flex items-center gap-2 mb-1">
      <span class="w-2 h-2 rounded-full" :class="dot"></span>
      <span class="font-medium text-gray-800">{{ risk.title }}</span>
      <span class="ml-auto text-xs text-gray-500">{{ risk.category }}</span>
    </div>
    <div class="text-gray-700">{{ risk.detail }}</div>
    <div v-if="risk.suggestion" class="text-gray-600 mt-1">
      <span class="font-medium">建议：</span>{{ risk.suggestion }}
    </div>
    <button
      class="text-xs text-brand-600 mt-2 underline"
      @click="emit('jump', risk.segment_id)"
    >
      定位原文 →
    </button>
  </div>
</template>
