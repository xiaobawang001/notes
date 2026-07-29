/**
 * Markdown 渲染 Composable
 * 封装 Vditor.md2html 异步渲染 + 图表后处理
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

/** 在已挂载的 DOM 容器中渲染图表（Mermaid / Graphviz / 思维导图 / 流程图） */
export function renderCharts(container: HTMLElement): void {
  // 按顺序调用各个图表渲染方法，避免互相干扰
  Vditor.mermaidRender(container, VDITOR_CDN, 'light')
  Vditor.graphvizRender(container, VDITOR_CDN)
  Vditor.mindmapRender(container, VDITOR_CDN, 'light')
  Vditor.flowchartRender(container, VDITOR_CDN)
  Vditor.chartRender(container, VDITOR_CDN, 'light')
}
