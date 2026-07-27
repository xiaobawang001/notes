import { nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

const CHART_LANGS = ['mermaid', 'graphviz', 'plantuml']
const HIGHLIGHT_RE = /\/\/\s*\[!code\s+(highlight|hl)\]\s*$/

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

const renderer = new marked.Renderer()

renderer.heading = function ({ text, depth }: any) {
  const slug = text.toLowerCase().replace(/<[^>]*>/g, '').replace(/[^\w\u4e00-\u9fff]+/g, '-').replace(/^-+|-+$/g, '')
  return `<h${depth} id="${slug}">${text}<a class="heading-anchor" href="#${slug}" aria-hidden="true">#</a></h${depth}>`
}

renderer.code = function ({ text, lang }: any) {
  const rawCode = text || ''
  const langName = (lang || '').toLowerCase()

  if (CHART_LANGS.includes(langName)) {
    return `<div class="chart-wrapper" data-lang="${langName}">${escapeHtml(rawCode)}</div>`
  }

  const lines = rawCode.split('\n')
  const highlightedLines = new Set<number>()
  const cleanLines: string[] = []
  for (let i = 0; i < lines.length; i++) {
    if (lines[i] && HIGHLIGHT_RE.test(lines[i])) {
      highlightedLines.add(i)
      cleanLines.push(lines[i].replace(HIGHLIGHT_RE, '').replace(/\s+$/, ''))
    } else {
      cleanLines.push(lines[i])
    }
  }
  const cleanCode = cleanLines.join('\n')

  let highlighted: string
  if (langName) {
    const validLang = hljs.getLanguage(langName) ? langName : 'plaintext'
    highlighted = hljs.highlight(cleanCode, { language: validLang, ignoreIllegals: true }).value
  } else {
    highlighted = escapeHtml(cleanCode)
  }

  const codeLines = highlighted.split('\n')
  const wrappedLines = codeLines.map((lineHtml, i) => {
    const hlClass = highlightedLines.has(i) ? ' highlighted' : ''
    return `<span class="code-line${hlClass}">${lineHtml || ' '}</span>`
  })

  const displayLang = langName || 'code'
  return [
    `<div class="code-block-wrapper" data-lang="${displayLang}">`,
    `  <div class="code-header">`,
    `    <span class="code-lang-label">${escapeHtml(displayLang)}</span>`,
    `    <div class="code-actions">`,
    `      <button class="code-btn" data-copy type="button" title="复制代码">`,
    `        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`,
    `        <span>复制</span>`,
    `      </button>`,
    `      <button class="code-btn" data-wrap type="button" title="换行切换">`,
    `        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 12H3"/><path d="m15 8 4 4-4 4"/><path d="M8 4v16"/></svg>`,
    `      </button>`,
    `      <button class="code-btn" data-fold type="button" title="折叠代码">`,
    `        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>`,
    `      </button>`,
    `    </div>`,
    `  </div>`,
    `  <div class="code-body">`,
    `    <pre><code class="hljs${langName ? ' language-' + langName : ''}">${wrappedLines.join('\n')}</code></pre>`,
    `  </div>`,
    `</div>`,
  ].join('\n')
}

marked.use({ renderer })

export function useMarkdown() {
  function render(content: string): string {
    return marked.parse(content || '') as string
  }

  function renderCharts(container: HTMLElement) {
    const mermaidBlocks = container.querySelectorAll<HTMLElement>('.chart-wrapper[data-lang="mermaid"]')
    for (const block of mermaidBlocks) {
      const div = document.createElement('div')
      div.className = 'mermaid'
      div.textContent = block.textContent || ''
      block.replaceWith(div)
    }
    if (mermaidBlocks.length) {
      import('mermaid').then((m) => { m.default.run({ nodes: document.querySelectorAll('.mermaid') }) })
    }
    const krokiBlocks = container.querySelectorAll<HTMLElement>('.chart-wrapper[data-lang="graphviz"], .chart-wrapper[data-lang="plantuml"]')
    for (const block of krokiBlocks) {
      const lang = block.getAttribute('data-lang') || 'graphviz'
      const img = document.createElement('img')
      img.className = 'kroki-chart'
      img.alt = `${lang} diagram`
      img.loading = 'lazy'
      img.src = `https://kroki.io/${lang}/svg/${btoa(unescape(encodeURIComponent(block.textContent || '')))}`
      img.onerror = () => { img.style.display = 'none' }
      block.replaceWith(img)
    }
  }

  return { render, renderCharts }
}
