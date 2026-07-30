/**
 * Markdown 渲染 Composable
 * 封装 Vditor.md2html 异步渲染 + 代码块/图表后处理
 */
import Vditor from 'vditor'

/** Vditor 默认 CDN 地址，用于加载图表等外部资源 */
const VDITOR_CDN = 'https://unpkg.com/vditor@3.11.2'

/** 将 Markdown 文本渲染为 HTML 字符串 */
export async function renderMarkdown(content: string): Promise<string> {
  if (!content) return ''
  return Vditor.md2html(content, {
    mode: 'light',
    hljs: { style: 'github', lineNumber: true },
    markdown: {
      autoSpace: true,
      fixTermTypo: true,
      mark: true,
      gfmAutoLink: true,
    },
    anchor: 2,
  })
}

/** 代码块后处理：行号高亮 + 复制按钮 + 语言标签 + 外层容器 */
export function renderCodeBlocks(container: HTMLElement): void {
  // 1. 添加语法高亮和行号（hljs 异步加载）
  Vditor.highlightRender(
    { style: 'github', lineNumber: true },
    container,
    VDITOR_CDN,
  )

  // 2. 添加复制按钮（.vditor-copy 被插入到 <pre> 内部）
  Vditor.codeRender(container)

  // 3. 为代码块添加外层容器和语言标签头部栏（使用内联样式）
  container.querySelectorAll('pre').forEach((pre) => {
    const code = pre.querySelector('code[class*="language-"]')
    if (!code) return
    if (pre.parentElement?.classList.contains('vditor-code-wrapper')) return

    const langMatch = code.className.match(/language-(\w+)/)
    const lang = langMatch ? langMatch[1] : ''

    // 外层容器（内联样式）
    const wrapper = document.createElement('div')
    wrapper.style.cssText = 'margin:1em 0;border:1px solid var(--yuque-border,#e7e9e8);border-radius:8px;overflow:hidden;background:var(--yuque-code-header-bg,#eef0ef)'

    // 头部栏
    const header = document.createElement('div')
    header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;height:36px;padding:0 10px 0 16px;border-bottom:1px solid var(--yuque-border-light,#eff0f0);background:var(--yuque-code-header-bg,#eef0ef);user-select:none'

    // 语言标签
    const langLabel = document.createElement('span')
    langLabel.style.cssText = 'font-size:12px;color:var(--yuque-text-secondary,#8a8f8d);font-family:Consolas,Monaco,monospace;font-weight:500'
    langLabel.textContent = lang
    header.appendChild(langLabel)

    // 把 .vditor-copy 移到头部栏右侧
    const copyEl = pre.querySelector('.vditor-copy') as HTMLElement | null
    if (copyEl) {
      // 隐藏 textarea
      const ta = copyEl.querySelector('textarea') as HTMLElement | null
      if (ta) ta.style.display = 'none'
      // 美化复制按钮
      const btn = copyEl.querySelector('span') as HTMLElement | null
      if (btn) {
        btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:4px;cursor:pointer;color:var(--yuque-text-secondary,#8a8f8d)'
      }
      const svg = copyEl.querySelector('svg') as HTMLElement | null
      if (svg) svg.style.cssText = 'width:14px;height:14px'
      copyEl.style.display = 'flex'
      copyEl.style.alignItems = 'center'
      header.appendChild(copyEl)
    }

    // 去掉 pre 自带样式
    pre.style.cssText = 'margin:0!important;border:none!important;border-radius:0!important;background:transparent!important'

    // 去掉 code 背景
    ;(code as HTMLElement).style.background = 'transparent'

    // 包装
    const parent = pre.parentElement!
    parent.insertBefore(wrapper, pre)
    wrapper.appendChild(header)
    wrapper.appendChild(pre)
  })
}

/** 在已挂载的 DOM 容器中渲染图表（Mermaid / Graphviz / 思维导图 / 流程图等） */
export function renderCharts(container: HTMLElement): void {
  Vditor.mermaidRender(container, VDITOR_CDN, 'light')
  Vditor.graphvizRender(container, VDITOR_CDN)
  Vditor.mindmapRender(container, VDITOR_CDN, 'light')
  Vditor.flowchartRender(container, VDITOR_CDN)
  Vditor.chartRender(container, VDITOR_CDN, 'light')
}
