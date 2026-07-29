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
    `      <button class="code-btn" data-copy type="button" title="复制代码" aria-label="复制代码">`,
    `        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`,
    `        <span>复制</span>`,
    `      </button>`,
    `      <button class="code-btn code-btn-icon" data-wrap type="button" title="换行切换" aria-label="换行">`,
    `        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M3 12h15a3 3 0 1 1 0 6h-4M16 16l-2 2 2 2M3 18h7"/></svg>`,
    `      </button>`,
    `      <button class="code-btn code-btn-icon" data-fold type="button" title="折叠代码" aria-label="折叠">`,
    `        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
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

  async function renderCharts(container: HTMLElement) {
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
    // ── Graphviz：本地 WASM 渲染 ──
    const graphvizBlocks = container.querySelectorAll<HTMLElement>('.chart-wrapper[data-lang="graphviz"]')
    if (graphvizBlocks.length) {
      try {
        const viz = await import('@viz-js/viz')
        const instance = await viz.instance()
        for (const block of graphvizBlocks) {
          const source = block.textContent || ''
          if (!source.trim()) continue
          try {
            const svg = instance.renderSVGElement(source)
            const wrapper = document.createElement('div')
            wrapper.className = 'graphviz-diagram'
            wrapper.appendChild(svg)
            block.replaceWith(wrapper)
          } catch (e) {
            block.replaceWith(document.createTextNode(`[Graphviz 渲染失败]`))
          }
        }
      } catch (e) {
        console.warn('[graphviz] WASM 加载失败:', e)
      }
    }

    // ── PlantUML：Kroki API ──
    const plantumlBlocks = container.querySelectorAll<HTMLElement>('.chart-wrapper[data-lang="plantuml"]')
    if (plantumlBlocks.length) {
      const { encode } = await import('plantuml-encoder')
      for (const block of plantumlBlocks) {
        const source = block.textContent || ''
        const img = document.createElement('img')
        img.className = 'plantuml-diagram'
        img.alt = 'PlantUML 图表'
        img.loading = 'lazy'
        img.src = `https://kroki.io/plantuml/svg/${encode(source)}`
        img.onerror = () => { img.style.display = 'none' }
        block.replaceWith(img)
      }
    }
  }

  return { render, renderCharts }
}
