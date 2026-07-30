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
  // 1. 添加语法高亮和行号（hljs 会异步加载）
  Vditor.highlightRender(
    { style: 'github', lineNumber: true },
    container,
    VDITOR_CDN,
  )

  // 2. 添加复制按钮（.vditor-copy 会被插入到 <pre> 内部，作为 <code> 的前一个兄弟）
  Vditor.codeRender(container)

  // 3. 为代码块添加外层容器和语言标签头部栏
  container.querySelectorAll('pre').forEach((pre) => {
    // 跳过图表类代码块
    const code = pre.querySelector('code[class*="language-"]')
    if (!code) return

    // 已包装过则跳过
    if (pre.parentElement?.classList.contains('vditor-code-wrapper')) return

    // 提取语言名（兼容 hljs 重构后的 class）
    const langMatch = code.className.match(/language-(\w+)/)
    const lang = langMatch ? langMatch[1] : ''

    // 创建外层容器
    const wrapper = document.createElement('div')
    wrapper.className = 'vditor-code-wrapper'

    // 创建头部栏（含语言标签 + 复制按钮）
    const header = document.createElement('div')
    header.className = 'vditor-code-header'

    const langLabel = document.createElement('span')
    langLabel.className = 'vditor-code-lang'
    langLabel.textContent = lang
    header.appendChild(langLabel)

    // 把 .vditor-copy 复制按钮从 pre 内部挪到头部栏右侧
    const copyEl = pre.querySelector('.vditor-copy')
    if (copyEl) {
      // .vditor-copy 是 <code> 的前一个兄弟，需要把它移到 pre 外面
      header.appendChild(copyEl)
    }

    // 包装结构：父节点 → wrapper → (header + pre)
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