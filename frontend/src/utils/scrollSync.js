/**
 * 段落级同步滚动。
 * 原理：两个容器各自对段落加 data-anchor-id="seg_xxx"。
 * 监听其中一个滚动，找到 viewport 顶部所在段落，在对方容器 scrollTo 对应段落。
 */
export function bindSyncScroll(leftEl, rightEl) {
  let lock = null
  let raf = 0

  const findTopAnchor = (container) => {
    const anchors = container.querySelectorAll('[data-anchor-id]')
    const top = container.getBoundingClientRect().top
    let best = null
    let bestDelta = Infinity
    for (const a of anchors) {
      const r = a.getBoundingClientRect()
      const delta = Math.abs(r.top - top)
      if (r.bottom >= top && delta < bestDelta) {
        bestDelta = delta
        best = a
      }
    }
    return best
  }

  const syncFrom = (from, to) => {
    if (lock === to) return
    lock = from
    cancelAnimationFrame(raf)
    raf = requestAnimationFrame(() => {
      const anchor = findTopAnchor(from)
      if (!anchor) {
        lock = null
        return
      }
      const id = anchor.getAttribute('data-anchor-id')
      const target = to.querySelector(`[data-anchor-id="${CSS.escape(id)}"]`)
      if (target) {
        const fromRect = anchor.getBoundingClientRect()
        const fromContainerTop = from.getBoundingClientRect().top
        const offset = fromRect.top - fromContainerTop
        const targetRect = target.getBoundingClientRect()
        const toContainerTop = to.getBoundingClientRect().top
        const delta = targetRect.top - toContainerTop - offset
        to.scrollTop += delta
      }
      // 稍后解锁
      setTimeout(() => {
        lock = null
      }, 80)
    })
  }

  const onLeft = () => syncFrom(leftEl, rightEl)
  const onRight = () => syncFrom(rightEl, leftEl)

  leftEl.addEventListener('scroll', onLeft, { passive: true })
  rightEl.addEventListener('scroll', onRight, { passive: true })

  return () => {
    leftEl.removeEventListener('scroll', onLeft)
    rightEl.removeEventListener('scroll', onRight)
    cancelAnimationFrame(raf)
  }
}

export function scrollToAnchor(container, anchorId, highlight = true) {
  if (!container) return
  const el = container.querySelector(`[data-anchor-id="${CSS.escape(anchorId)}"]`)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  if (highlight) {
    el.classList.remove('is-highlight')
    // 触发动画
    void el.offsetWidth
    el.classList.add('is-highlight')
    setTimeout(() => el.classList.remove('is-highlight'), 2000)
  }
}
