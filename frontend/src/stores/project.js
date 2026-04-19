import { defineStore } from 'pinia'
import {
  listSegments,
  openTranslateStream,
  scanRisks,
  listRisks,
  retrySegment
} from '../api'

export const useProjectStore = defineStore('project', {
  state: () => ({
    project: null,
    segments: [], // [{id, seq, clause_no, heading, original_md, translated_md, status, error, token_count}]
    segmentMap: {}, // id → segment
    risks: [],
    translating: false,
    scanningRisk: false,
    fatalError: ''
  }),

  actions: {
    reset() {
      this.project = null
      this.segments = []
      this.segmentMap = {}
      this.risks = []
      this.translating = false
      this.scanningRisk = false
      this.fatalError = ''
    },

    async loadSegments(projectId) {
      const rows = await listSegments(projectId)
      this.segments = rows
      this.segmentMap = Object.fromEntries(rows.map((r) => [r.id, r]))
    },

    async startTranslation(projectId, onAllDone) {
      if (this.translating) return
      this.translating = true
      this.fatalError = ''
      openTranslateStream(projectId, {
        onStart: ({ segment_id }) => {
          const s = this.segmentMap[segment_id]
          if (s) {
            s.status = 'streaming'
            s.translated_md = ''
            s.error = null
          }
        },
        onDelta: ({ segment_id, delta }) => {
          const s = this.segmentMap[segment_id]
          if (s) {
            s.translated_md = (s.translated_md || '') + delta
          }
        },
        onDone: ({ segment_id, full_text }) => {
          const s = this.segmentMap[segment_id]
          if (s) {
            s.translated_md = full_text
            s.status = 'done'
          }
        },
        onError: ({ segment_id, error }) => {
          const s = this.segmentMap[segment_id]
          if (s) {
            s.status = 'failed'
            s.error = error
          }
        },
        onAllDone: (info) => {
          this.translating = false
          onAllDone && onAllDone(info)
        },
        onFatal: ({ error }) => {
          this.translating = false
          this.fatalError = error
        }
      })
    },

    async retryOne(segmentId) {
      const s = this.segmentMap[segmentId]
      if (!s) return
      s.status = 'streaming'
      s.translated_md = ''
      s.error = null
      try {
        const res = await retrySegment(segmentId)
        s.translated_md = res.translated_md
        s.status = 'done'
      } catch (e) {
        s.status = 'failed'
        s.error = e.message
      }
    },

    async scanRisks(projectId) {
      this.scanningRisk = true
      try {
        const res = await scanRisks(projectId)
        this.risks = res.items
      } finally {
        this.scanningRisk = false
      }
    },

    async loadRisks(projectId) {
      const res = await listRisks(projectId)
      this.risks = res.items
    }
  }
})
