/**
 * Markdown 渲染 composable — 基于 Vditor 渲染管线
 *
 * - Vditor.md2html()：Markdown 解析 + 渲染（图表保留 div.language-* 结构）
 * - Vditor.mermaidRender/graphvizRender/plantumlRender：图表渲染
 * - 本地 hljs：高亮代码（避开 Vditor 的 CDN 依赖）
 * - 后处理：把代码块包装为带按钮的 HTML
 */
import Vditor from 'vditor'
import hljs from 'highlight.js/lib/core'

// 按需加载语言
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import shell from 'highlight.js/lib/languages/shell'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import scss from 'highlight.js/lib/languages/scss'
import sql from 'highlight.js/lib/languages/sql'
import yaml from 'highlight.js/lib/languages/yaml'
import markdown from 'highlight.js/lib/languages/markdown'
import dockerfile from 'highlight.js/lib/languages/dockerfile'
import nginx from 'highlight.js/lib/languages/nginx'
import plaintext from 'highlight.js/lib/languages/plaintext'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('shell', shell)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('vue', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('scss', scss)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('md', markdown)
hljs.registerLanguage('dockerfile', dockerfile)
hljs.registerLanguage('nginx', nginx)
hljs.registerLanguage('plaintext', plaintext)
hljs.registerLanguage('text', plaintext)

// Vditor 会从 CDN 加载 highlight.js，强制覆盖为我们本地的
;(window as any).hljs = hljs

const HIGHLIGHT_RE = /\/\/\s*\[!code\s+(highlight|hl)\]\s*$/

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/** 把源码 + 语言转换为带行号 + 高亮的 HTML 字符串 */
function buildCodeBlockHTML(rawCode: string, lang: string) {
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
    `      <button class="code-block-btn" data-copy type="button" title="复制代码"><span class="label">复制</span></button>`,
    `      <button class="code-block-btn icon-only" data-wrap type="button" title="切换换行"><span class="label">换行</span></button>`,
    `      <button class="code-block-btn icon-only" data-fold type="button" title="折叠代码"><span class="label">折叠</span></button>`,
    `    </div>`,
    `  </div>`,
    `  <div class="code-block-body"><pre class="hljs code-with-line-number"><code class="language-${escapeHtml(displayLang)} hljs">${linesHtml}</code></pre></div>`,
    `</div>`,
  ].join('\n')
}

/** 后处理 Vditor 输出 HTML
 *  - 处理 <pre><code>：添加行号/高亮 + 自定义按钮 wrapper
 *  - 处理 <div class="language-xxx"> 图表块：保留，让 renderCharts 调用 Vditor 原生渲染
 */
function postProcess(html: string): string {
  const tmp = document.createElement('div')
  tmp.innerHTML = html

  // 处理所有 pre>code 代码块
  const pres = Array.from(tmp.querySelectorAll('pre'))
  for (const pre of pres) {
    const code = pre.querySelector('code')
    if (!code) continue
    const classMatch = code.className.match(/language-(\w+)/)
    const lang = (classMatch?.[1] || '').toLowerCase()
    const rawCode = code.textContent || ''

    // graphviz/dot：当作图表处理，转为 div.language-graphviz 让 Vditor 渲染
    if (lang === 'dot' || lang === 'graphviz') {
      const div = document.createElement('div')
      div.className = 'language-graphviz'
      div.textContent = rawCode
      pre.replaceWith(div)
      continue
    }

    // mermaid/plantuml（如果 Vditor 输出为 <pre> 形式）：同上
    if (lang === 'mermaid' || lang === 'plantuml') {
      const div = document.createElement('div')
      div.className = `language-${lang}`
      div.textContent = rawCode
      pre.replaceWith(div)
      continue
    }

    // 普通代码块：包装为我们的按钮结构 + 本地 hljs 高亮
    const html2 = buildCodeBlockHTML(rawCode, lang)
    const wrapper = document.createElement('div')
    wrapper.innerHTML = html2
    pre.replaceWith(wrapper.firstElementChild || pre)
  }

  return tmp.innerHTML
}

export function useMarkdown() {
  /** Markdown → HTML */
  async function render(content: string): Promise<string> {
    if (!content) return ''
    try {
      const html = await Vditor.md2html(content, {
        mode: 'light',
        anchor: 2,
        hljs: { enable: false }, // 关闭 Vditor CDN 高亮，自己处理
        markdown: {
          toc: false,
          footnotes: true,
          autoSpace: true,
        },
      })
      return postProcess(html)
    } catch (e) {
      console.error('[Vditor md2html]', e)
      return `<p style="color:#c00">渲染失败：${escapeHtml(String(e))}</p>`
    }
  }

  /** 渲染图表（容器是文章正文 DOM） */
  async function renderCharts(container: HTMLElement) {
    // Vditor 原生图表渲染器查找 .language-* div
    Vditor.mermaidRender(container)
    Vditor.graphvizRender(container)
    Vditor.plantumlRender(container)
  }

  return { render, renderCharts }
}
