/**
 * Markdown 渲染 composable — 基于 Vditor 原生渲染管线
 *
 * 代码块：Vditor.codeRender() 提供复制按钮 + 行号 + 语法高亮
 * 图表：Vditor.mermaidRender / graphvizRender / plantumlRender
 * 标题锚点：Vditor anchor 选项（原生支持）
 */
import Vditor from 'vditor'

/** 对代码块添加自定义操作按钮（换行 / 折叠）并后处理行高亮 */
function enhanceCodeBlocks(container: HTMLElement) {
  // 先用 Vditor 的 codeRender 添加复制按钮 + 确保高亮
  Vditor.codeRender(container)

  // 对每个代码块添加换行/折叠按钮 + 行高亮标记
  container.querySelectorAll<HTMLElement>('.vditor-copy').forEach((copyBtn) => {
    const pre = copyBtn.parentElement
    if (!pre) return

    // 避免重复注入
    if (pre.querySelector('[data-wrap-btn]')) return

    // 换行按钮
    const wrapBtn = document.createElement('button')
    wrapBtn.setAttribute('data-wrap-btn', '')
    wrapBtn.className = 'vditor-copy'
    wrapBtn.title = '换行切换'
    wrapBtn.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M3 12h15a3 3 0 1 1 0 6h-4M16 16l-2 2 2 2M3 18h7"/></svg>'
    wrapBtn.onclick = () => pre.classList.toggle('vditor-code--wrap')

    // 折叠按钮
    const foldBtn = document.createElement('button')
    foldBtn.setAttribute('data-fold-btn', '')
    foldBtn.className = 'vditor-copy'
    foldBtn.title = '折叠代码'
    foldBtn.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>'
    foldBtn.onclick = () => pre.classList.toggle('vditor-code--fold')

    copyBtn.before(foldBtn, wrapBtn)

    // 行高亮：// [!code highlight] 标记
    pre.querySelectorAll<HTMLElement>('.vditor-linenumber__rows > span').forEach((line) => {
      const text = line.textContent || ''
      if (text.includes('// [!code highlight]') || text.includes('// [!code hl]')) {
        line.classList.add('vditor-code--highlight')
        // 移除高亮注释文本
        const code = line.querySelector('code') || line
        code.innerHTML = code.innerHTML.replace(/\/\/\s*\[!code\s+(highlight|hl)\]\s*/, '')
      }
    })
  })
}

export function useMarkdown() {
  /** 渲染 Markdown → HTML（Vditor 异步引擎） */
  async function render(content: string): Promise<string> {
    if (!content) return ''
    return await Vditor.md2html(content, {
      mode: 'light',
      anchor: 2,        // 标题锚点放在标题后面
      hljs: {
        style: 'github',
        lineNumber: true,
      },
      markdown: {
        toc: false,
        footnotes: true,
        autoSpace: true,
      },
    })
  }

  /** 初始化代码块增强 + 图表渲染 */
  async function renderCharts(container: HTMLElement) {
    // 代码块增强（复制 + 换行 + 折叠 + 行高亮）
    enhanceCodeBlocks(container)

    // 图表渲染（Vditor 内置）
    Vditor.mermaidRender(container)
    Vditor.graphvizRender(container)
    Vditor.plantumlRender(container)
  }

  return { render, renderCharts }
}
