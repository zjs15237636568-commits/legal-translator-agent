import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({
  gfm: true,
  breaks: false
})

export function renderMarkdown(md) {
  if (!md) return ''
  const raw = marked.parse(md)
  return DOMPurify.sanitize(raw)
}

/** 把 [Clause 3.1] / [§12] 替换为可点击的 <a>. 传入 citations 数组可绑定 segment_id */
export function renderAnswerWithCitations(text, citations = []) {
  if (!text) return ''
  const escaped = renderMarkdown(text)
  // 构建 label → segment_id 映射（以 citations 为准）
  const map = {}
  for (const c of citations) {
    map[c.label] = c.segment_id
  }
  const re = /\[(?:Clause\s+[\d.]+|§\d+)\]/gi
  return escaped.replace(re, (m) => {
    const segId = map[m]
    if (!segId) {
      return `<span class="citation-link">${m}</span>`
    }
    return `<a class="citation-link" data-cite="${segId}">${m}</a>`
  })
}
