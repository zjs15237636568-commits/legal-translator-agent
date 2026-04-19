<script setup>
import { onMounted, onBeforeUnmount, ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useProjectStore } from '@/stores/project'
import { getProject, exportDocxUrl } from '@/api'
import SegmentList from '@/components/SegmentList.vue'
import RiskCard from '@/components/RiskCard.vue'
import ChatBox from '@/components/ChatBox.vue'
import { bindSyncScroll, scrollToAnchor } from '@/utils/scrollSync'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const store = useProjectStore()
const { segments, risks, translating, scanningRisk, fatalError } = storeToRefs(store)

const project = ref(null)
const leftPane = ref(null)
const rightPane = ref(null)
let unbind = null

const progress = computed(() => {
  if (!segments.value.length) return { done: 0, total: 0, pct: 0 }
  const done = segments.value.filter((s) => s.status === 'done').length
  const total = segments.value.length
  return { done, total, pct: total ? Math.round((done / total) * 100) : 0 }
})

const canScanRisks = computed(
  () => !translating.value && progress.value.total > 0 && progress.value.done === progress.value.total
)

async function init() {
  store.reset()
  project.value = await getProject(props.id)
  await store.loadSegments(props.id)
  await store.loadRisks(props.id)
  await nextTick()
  if (leftPane.value && rightPane.value) {
    unbind = bindSyncScroll(leftPane.value, rightPane.value)
  }
  // 若存在未完成段落，自动开始翻译
  const hasPending = segments.value.some((s) => s.status !== 'done')
  if (hasPending) {
    store.startTranslation(props.id)
  }
}

onMounted(init)
onBeforeUnmount(() => {
  unbind && unbind()
})

function jumpToSegment(segmentId) {
  scrollToAnchor(leftPane.value, segmentId)
  scrollToAnchor(rightPane.value, segmentId, false)
}

async function doScanRisks() {
  await store.scanRisks(props.id)
}

function doExport() {
  window.open(exportDocxUrl(props.id), '_blank')
}

async function retryOne(segmentId) {
  await store.retryOne(segmentId)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 子工具条 -->
    <div class="h-11 shrink-0 bg-white border-b flex items-center px-4 gap-3 text-sm">
      <button class="text-gray-500 hover:text-gray-700" @click="router.push('/history')">
        ← 返回
      </button>
      <div class="font-medium text-gray-800 truncate max-w-[380px]">
        {{ project?.name || '—' }}
      </div>
      <span class="text-xs text-gray-500">
        {{ progress.done }}/{{ progress.total }} 段 · {{ progress.pct }}%
      </span>
      <span v-if="translating" class="text-xs text-blue-600">翻译中…</span>
      <span v-if="fatalError" class="text-xs text-red-600">{{ fatalError }}</span>

      <div class="ml-auto flex items-center gap-2">
        <button
          class="btn-secondary"
          :disabled="!canScanRisks || scanningRisk"
          @click="doScanRisks"
        >
          {{ scanningRisk ? '扫描中…' : '风险扫描' }}
        </button>
        <button class="btn-secondary" @click="doExport">导出 Word</button>
      </div>
    </div>

    <!-- 三栏主区 -->
    <div class="flex-1 min-h-0 flex">
      <section class="flex-[4] min-w-0 border-r bg-white flex flex-col">
        <div class="h-9 shrink-0 border-b px-3 flex items-center text-xs text-gray-500">
          原文 (English)
        </div>
        <div ref="leftPane" class="flex-1 overflow-y-auto scrollbar-thin px-4 py-3">
          <SegmentList :segments="segments" side="original" />
        </div>
      </section>

      <section class="flex-[4] min-w-0 border-r bg-white flex flex-col">
        <div class="h-9 shrink-0 border-b px-3 flex items-center text-xs text-gray-500">
          译文（简体中文）
        </div>
        <div ref="rightPane" class="flex-1 overflow-y-auto scrollbar-thin px-4 py-3">
          <SegmentList
            :segments="segments"
            side="translation"
            @retry="retryOne"
          />
        </div>
      </section>

      <aside class="flex-[2] min-w-[260px] bg-white flex flex-col">
        <!-- 风险区 -->
        <div class="flex flex-col h-1/2 border-b">
          <div class="h-9 shrink-0 border-b px-3 flex items-center text-xs text-gray-500">
            风险提示（{{ risks.length }}）
          </div>
          <div class="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-2">
            <div v-if="!risks.length" class="text-xs text-gray-400">
              翻译完成后点击"风险扫描"生成风险卡片。
            </div>
            <RiskCard
              v-for="r in risks"
              :key="r.id"
              :risk="r"
              @jump="jumpToSegment"
            />
          </div>
        </div>
        <!-- Q&A 区 -->
        <div class="flex-1 min-h-0">
          <ChatBox :project-id="id" @jump="jumpToSegment" />
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.btn-secondary {
  @apply px-3 py-1 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm;
}
</style>
