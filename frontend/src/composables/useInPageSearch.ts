const SKIP_SELECTOR = 'pre, code, .mermaid, .kroki-chart, .heading-anchor, .heading-anchor-share'
const HIT_CLASS = 'in-page-search-hit'
const CURRENT_CLASS = 'is-current'

let marks: HTMLElement[] = []
let currentIndex = -1

function clearHighlights() {
  marks.forEach((mark) => {
    const parent = mark.parentNode
    if (!parent) return
    parent.replaceChild(document.createTextNode(mark.textContent ?? ''), mark)
    parent.normalize()
  })
  marks = []
  currentIndex = -1
}

function collectTextNodes(root: HTMLElement): Text[] {
  const nodes: Text[] = []
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.textContent?.trim()) return NodeFilter.FILTER_REJECT
      const parent = node.parentElement
      if (!parent || !parent.closest('.vp-doc')) return NodeFilter.FILTER_REJECT
      if (parent.closest(SKIP_SELECTOR)) return NodeFilter.FILTER_REJECT
      return NodeFilter.FILTER_ACCEPT
    },
  })
  let current = walker.nextNode()
  while (current) {
    nodes.push(current as Text)
    current = walker.nextNode()
  }
  return nodes
}

function highlightInTextNode(textNode: Text, query: string) {
  const text = textNode.textContent ?? ''
  const lowerText = text.toLowerCase()
  const lowerQuery = query.toLowerCase()
  let start = 0
  let index = lowerText.indexOf(lowerQuery, start)
  if (index === -1) return

  const fragment = document.createDocumentFragment()
  while (index !== -1) {
    if (index > start) {
      fragment.appendChild(document.createTextNode(text.slice(start, index)))
    }
    const mark = document.createElement('mark')
    mark.className = HIT_CLASS
    mark.textContent = text.slice(index, index + query.length)
    fragment.appendChild(mark)
    marks.push(mark)
    start = index + query.length
    index = lowerText.indexOf(lowerQuery, start)
  }
  if (start < text.length) {
    fragment.appendChild(document.createTextNode(text.slice(start)))
  }
  textNode.parentNode?.replaceChild(fragment, textNode)
}

function activateMark(index: number) {
  marks.forEach((mark, i) => mark.classList.toggle(CURRENT_CLASS, i === index))
  const current = marks[index]
  if (!current) return
  const navHeight = 56
  const offset = navHeight + 16
  const top = current.getBoundingClientRect().top + window.scrollY - offset
  window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
}

export function runInPageSearch(query: string): number {
  clearHighlights()
  const doc = document.querySelector<HTMLElement>('.vp-doc')
  if (!doc || !query.trim()) return 0

  const textNodes = collectTextNodes(doc)
  textNodes.forEach((node) => highlightInTextNode(node, query.trim()))
  if (marks.length > 0) {
    currentIndex = 0
    activateMark(currentIndex)
  }
  return marks.length
}

export function gotoNextMatch() {
  if (!marks.length) return
  currentIndex = (currentIndex + 1) % marks.length
  activateMark(currentIndex)
}

export function gotoPrevMatch() {
  if (!marks.length) return
  currentIndex = (currentIndex - 1 + marks.length) % marks.length
  activateMark(currentIndex)
}

export function clearInPageSearch() { clearHighlights() }
export function getMatchCount() { return marks.length }
export function getCurrentMatchIndex() { return marks.length ? currentIndex + 1 : 0 }
