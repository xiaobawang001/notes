/**
 * Markdown 渲染 composable — 基于 Vditor
 * 替换 marked + highlight.js，使用 Vditor.md2html() 解析，
 * 后处理代码块/图表以保留自定义功能。
 */
import Vditor from 'vditor'

const CHART_LANGS = ['mermaid', 'graphviz', 'plantuml']
const HIGHLIGHT_RE = /\/\/\s*\[!code\s+(highlight|hl)\]\s*$/

// ── 工具函数 ──
function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/** 将 Vditor 生成的 <pre><code> 包装为自定义 code-block-wrapper */
function wrapCodeBlock(pre: HTMLElement): string {
  const code = pre.querySelector('code')
  if (!code) return pre.outerHTML

  // 提取语言
  const classMatch = code.className.match(/language-(\w+)/)
  const lang = classMatch?.[1] || ''

  // 图表语言 → 包裹为 chart-wrapper，由 renderCharts 处理
  if (lang && CHART_LANGS.includes(lang)) {
    const rawCode = code.textContent || ''
    return `<div class="chart-wrapper" data-lang="${lang}">${escapeHtml(rawCode)}</div>`
  }

  // 提取源码（从 hljs 渲染后的 HTML 中还原纯文本）
  const rawLines: string[] = []
  code.querySelectorAll('.code-line, .hljs-ln-line').forEach((line) => {
    rawLines.push(line.textContent || '')
  })
  // 如果没有 .code-line span，直接取 textContent 按行分割
  const sourceLines = rawLines.length > 0 ? rawLines : (code.textContent || '').split('\n')
  // 去掉末尾空行
  while (sourceLines.length && !sourceLines[sourceLines.length - 1].trim()) sourceLines.pop()

  // 行高亮标记处理
  const highlightedLines = new Set<number>()
  const cleanLines: string[] = []
  for (let i = 0; i < sourceLines.length; i++) {
    if (sourceLines[i] && HIGHLIGHT_RE.test(sourceLines[i])) {
      highlightedLines.add(i)
      cleanLines.push(sourceLines[i].replace(HIGHLIGHT_RE, '').replace(/\s+$/, ''))
    } else {
      cleanLines.push(sourceLines[i])
    }
  }

  // 重新用 Vditor 高亮纯代码（保持语法着色）
  const cleanCode = cleanLines.join('\n')
  let highlighted: string
  if (lang && lang !== 'plaintext') {
    try {
      // Vditor 内置 highlight.js，直接用它
      const hljs = (window as any).hljs
      if (hljs?.getLanguage?.(lang)) {
        highlighted = hljs.highlight(cleanCode, { language: lang, ignoreIllegals: true }).value
      } else {
        highlighted = escapeHtml(cleanCode)
      }
    } catch {
      highlighted = escapeHtml(cleanCode)
    }
  } else {
    highlighted = escapeHtml(cleanCode)
  }

  // 构建代码行（含行号和高亮标记）
  const codeLines = highlighted.split('\n')
  const wrappedLines = codeLines.map((lineHtml, i) => {
    const hlClass = highlightedLines.has(i) ? ' highlighted' : ''
    return `<span class="code-line${hlClass}">${lineHtml || ' '}</span>`
  })

  const displayLang = lang || 'code'
  return [
    `<div class="code-block-wrapper" data-lang="${escapeHtml(displayLang)}">`,
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
    `    <pre><code class="hljs${lang ? ' language-' + lang : ''}">${wrappedLines.join('\n')}</code></pre>`,
    `  </div>`,
    `</div>`,
  ].join('\n')
}

/** 后处理 Vditor 输出的 HTML */
function postProcess(html: string): string {
  // 用临时 DOM 解析
  const tmp = document.createElement('div')
  tmp.innerHTML = html

  // 处理所有代码块
  const pres = Array.from(tmp.querySelectorAll('pre'))
  for (const pre of pres) {
    const code = pre.querySelector('code')
    if (!code) continue

    const classMatch = code.className.match(/language-(\w+)/)
    const lang = classMatch?.[1] || ''

    if (lang && CHART_LANGS.includes(lang)) {
      // 图表 → chart-wrapper
      const rawCode = code.textContent || ''
      const wrapper = document.createElement('div')
      wrapper.className = 'chart-wrapper'
      wrapper.setAttribute('data-lang', lang)
      wrapper.textContent = rawCode
      pre.replaceWith(wrapper)
    } else {
      // 普通代码块 → 用 wrapper HTML 替换
      const wrapper = document.createElement('div')
      wrapper.innerHTML = wrapCodeBlock(pre)
      pre.replaceWith(wrapper.firstElementChild || pre)
    }
  }

  return tmp.innerHTML
}

export function useMarkdown() {
  /** 渲染 Markdown → HTML（异步，Vditor.md2html 返回 Promise） */
  async function render(content: string): Promise<string> {
    if (!content) return ''
    const html = await Vditor.md2html(content || '', {
      mode: 'light',
    })
    return postProcess(html)
  }

  /** 渲染图表（mermaid / graphviz / plantuml） */
  async function renderCharts(container: HTMLElement) {
    // ── Mermaid ──
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

    // ── Graphviz：本地 WASM ──
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
          } catch {
            block.replaceWith(document.createTextNode('[Graphviz 渲染失败]'))
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
