/**
 * Markdown 渲染 composable — 基于 Vditor 渲染管线
 *
 * - Vditor.md2html()：Markdown 解析 + 渲染
 * - Vditor.*Render：图表渲染 (mermaid/graphviz/plantuml/echarts/mindmap/flowchart)
 * - 本地 hljs：代码高亮（避开 Vditor CDN 依赖）
 * - 后处理：代码块包装 + 行号 + 自定义按钮（复制/换行/折叠）
 */
import Vditor from 'vditor'
import hljs from 'highlight.js/lib/core'

// ── hljs 语言注册 ──
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import java from 'highlight.js/lib/languages/java'
import cpp from 'highlight.js/lib/languages/cpp'
import c from 'highlight.js/lib/languages/c'
import go_ from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import php from 'highlight.js/lib/languages/php'
import ruby from 'highlight.js/lib/languages/ruby'
import swift from 'highlight.js/lib/languages/swift'
import kotlin from 'highlight.js/lib/languages/kotlin'
import bash from 'highlight.js/lib/languages/bash'
import shell from 'highlight.js/lib/languages/shell'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import scss from 'highlight.js/lib/languages/scss'
import less from 'highlight.js/lib/languages/less'
import sql from 'highlight.js/lib/languages/sql'
import yaml from 'highlight.js/lib/languages/yaml'
import toml from 'highlight.js/lib/languages/ini' // toml ≈ ini 语法
import makefile from 'highlight.js/lib/languages/makefile'
import diff from 'highlight.js/lib/languages/diff'
import graphql from 'highlight.js/lib/languages/graphql'
import markdown from 'highlight.js/lib/languages/markdown'
import dockerfile from 'highlight.js/lib/languages/dockerfile'
import nginx from 'highlight.js/lib/languages/nginx'
import plaintext from 'highlight.js/lib/languages/plaintext'

const LANGS: [string, any][] = [
  ['javascript', javascript], ['js', javascript],
  ['typescript', typescript], ['ts', typescript],
  ['python', python], ['py', python],
  ['java', java],
  ['cpp', cpp], ['c++', cpp], ['cxx', cpp],
  ['c', c],
  ['go', go_], ['golang', go_],
  ['rust', rust], ['rs', rust],
  ['php', php],
  ['ruby', ruby], ['rb', ruby],
  ['swift', swift],
  ['kotlin', kotlin], ['kt', kotlin],
  ['bash', bash], ['shell', shell], ['sh', bash], ['zsh', bash],
  ['json', json],
  ['xml', xml], ['html', xml], ['vue', xml], ['svg', xml],
  ['css', css], ['scss', scss], ['less', less],
  ['sql', sql],
  ['yaml', yaml], ['yml', yaml],
  ['toml', toml], ['ini', toml],
  ['makefile', makefile],
  ['diff', diff], ['patch', diff],
  ['graphql', graphql], ['gql', graphql],
  ['markdown', markdown], ['md', markdown],
  ['dockerfile', dockerfile], ['docker', dockerfile],
  ['nginx', nginx],
  ['plaintext', plaintext], ['text', plaintext], ['txt', plaintext],
]
LANGS.forEach(([name, mod]) => hljs.registerLanguage(name, mod))
;(window as any).hljs = hljs

// ── 常量 ──
const CHART_LANGS = new Set(['mermaid', 'graphviz', 'plantuml', 'dot', 'echarts', 'flowchart', 'mindmap'])
const HIGHLIGHT_RE = /\/\/\s*\[!code\s+(highlight|hl)\]\s*$/
const COPY_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
const WRAP_ICON  = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M3 12h15a3 3 0 1 1 0 6h-4"/><path d="m16 16 2 2-2 2"/><path d="M3 18h7"/></svg>'
const FOLD_ICON  = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>'

// ── 工具函数 ──
function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/** 将纯源码 + 语言转换为带行号 + hljs 高亮的代码块 HTML */
function buildCodeBlockHTML(rawCode: string, lang: string): string {
  const sourceLines = rawCode.split('\n')
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
  while (cleanLines.length && !cleanLines[cleanLines.length - 1].trim()) cleanLines.pop()
  const cleanCode = cleanLines.join('\n')

  let highlightedHtml: string
  const validLang = lang && hljs.getLanguage(lang) ? lang : ''
  if (validLang) {
    try {
      highlightedHtml = hljs.highlight(cleanCode, { language: validLang, ignoreIllegals: true }).value
    } catch {
      highlightedHtml = escapeHtml(cleanCode)
    }
  } else {
    highlightedHtml = escapeHtml(cleanCode)
  }

  const codeLines = highlightedHtml.split('\n')
  const linesHtml = codeLines
    .map((lineHtml, i) => {
      const ln = i + 1
      const hlClass = highlightedLines.has(i) ? ' vditor-code--highlight' : ''
      return `<span class="line${hlClass}" data-line="${ln}"><span class="line-num">${ln}</span><span class="line-content">${lineHtml || ' '}</span></span>`
    })
    .join('\n')

  const displayLang = lang || 'plaintext'
  return [
    `<div class="code-block-wrapper" data-lang="${escapeHtml(displayLang)}">`,
    `  <div class="code-block-header">`,
    `    <span class="code-block-lang">${escapeHtml(displayLang)}</span>`,
    `    <div class="code-block-actions">`,
    `      <button class="code-block-btn" data-copy type="button" title="复制代码">${COPY_ICON}<span class="label">复制</span></button>`,
    `      <button class="code-block-btn" data-wrap type="button" title="切换换行">${WRAP_ICON}<span class="label">换行</span></button>`,
    `      <button class="code-block-btn" data-fold type="button" title="折叠代码">${FOLD_ICON}<span class="label">折叠</span></button>`,
    `    </div>`,
    `  </div>`,
    `  <div class="code-block-body"><pre class="hljs code-with-line-number"><code class="language-${escapeHtml(displayLang)} hljs">${linesHtml}</code></pre></div>`,
    `</div>`,
  ].join('\n')
}

/** 后处理 Vditor 输出 HTML */
function postProcess(html: string): string {
  const tmp = document.createElement('div')
  tmp.innerHTML = html

  // 处理 pre>code 代码块
  tmp.querySelectorAll('pre').forEach((pre) => {
    const code = pre.querySelector('code')
    if (!code) return
    const lang = (code.className.match(/language-(\w+)/)?.[1] || '').toLowerCase()
    const rawCode = code.textContent || ''

    // 图表/脑图语言 → 保留 language-* div 结构让 Vditor 渲染
    if (CHART_LANGS.has(lang)) {
      const div = document.createElement('div')
      const normLang = lang === 'dot' ? 'graphviz' : lang
      div.className = `language-${normLang}`
      div.textContent = rawCode
      pre.replaceWith(div)
      return
    }

    // 普通代码块 → wrapper
    const html2 = buildCodeBlockHTML(rawCode, lang)
    const wrapper = document.createElement('div')
    wrapper.innerHTML = html2
    pre.replaceWith(wrapper.firstElementChild!)
  })

  return tmp.innerHTML
}

// ── 导出 composable ──
export function useMarkdown() {
  /** Markdown → HTML */
  async function render(content: string): Promise<string> {
    if (!content) return ''
    try {
      const html = await Vditor.md2html(content, {
        mode: 'light',
        anchor: 2,
        hljs: { enable: false },
        markdown: {
          toc: false,
          footnotes: true,
          autoSpace: true,
          fixTermTypo: true,
          mark: true,
          sup: true,
          sub: true,
          paragraphBeginningSpace: false,
        },
      })
      return postProcess(html)
    } catch (e) {
      console.error('[Vditor md2html]', e)
      return `<p style="color:#c00">渲染失败：${escapeHtml(String(e))}</p>`
    }
  }

  /** 渲染图表/脑图 */
  async function renderCharts(container: HTMLElement) {
    Vditor.mermaidRender(container)
    Vditor.graphvizRender(container)
    Vditor.plantumlRender(container)
    Vditor.mindmapRender(container)
    Vditor.flowchartRender(container)
    Vditor.chartRender(container)
  }

  return { render, renderCharts }
}
