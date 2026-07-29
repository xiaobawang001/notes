<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Vditor from 'vditor'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const containerRef = ref<HTMLElement | null>(null)
let vditor: Vditor | null = null

onMounted(() => {
  if (!containerRef.value) return
  vditor = new Vditor(containerRef.value, {
    value: props.modelValue,
    mode: 'sv',
    height: 480,
    placeholder: '输入 Markdown 内容...',
    toolbar: [
      'headings', 'bold', 'italic', 'strike', '|',
      'line', 'quote', 'list', 'ordered-list', 'check', 'code', 'inline-code', '|',
      'upload', 'link', 'table', '|',
      'undo', 'redo', '|',
      'fullscreen', 'outline',
    ],
    toolbarConfig: { pin: true },
    counter: { enable: true, type: 'text' },
    preview: {
      mode: 'both',
      hljs: {
        style: 'github',
        lineNumber: true,
        // 自定义代码块操作栏：在 Vditor 内置复制按钮旁加换行/折叠
        renderMenu(_code: string, copy: string) {
          const wrapBtn = '<button class="vditor-copy" title="换行切换" data-wrap-btn><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M3 12h15a3 3 0 1 1 0 6h-4M16 16l-2 2 2 2M3 18h7"/></svg></button>'
          const foldBtn = '<button class="vditor-copy" title="折叠代码" data-fold-btn><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></button>'
          return `${foldBtn}${wrapBtn}${copy}`
        },
      },
      // 预览渲染完成后注入 Vditor 图表
      after() {
        const previewEl = containerRef.value?.querySelector('.vditor-preview') as HTMLElement
        if (!previewEl) return
        Vditor.mermaidRender(previewEl)
        Vditor.graphvizRender(previewEl)
        Vditor.plantumlRender(previewEl)
      },
    },
    after() {
      vditor?.setValue(props.modelValue)
    },
    input(value) {
      emit('update:modelValue', value)
    },
  })
})

watch(() => props.modelValue, (val) => {
  const editorVal = vditor?.getValue()
  if (editorVal !== val && vditor) {
    vditor.setValue(val)
  }
})

onBeforeUnmount(() => {
  vditor?.destroy()
})
</script>

<template>
  <div ref="containerRef" class="vditor-container" />
</template>

<style scoped>
.vditor-container {
  border: 1px solid var(--yuque-border);
  border-radius: 6px;
  overflow: hidden;
}
:deep(.vditor-toolbar) {
  background: var(--yuque-page-bg);
  border-bottom: 1px solid var(--yuque-border);
}
:deep(.vditor-toolbar__item) {
  color: var(--yuque-text-secondary);
}
:deep(.vditor-toolbar__item:hover) {
  background: var(--yuque-brand-soft);
}
:deep(.vditor-input) {
  background: var(--yuque-paper-bg);
  color: var(--yuque-text);
}
:deep(.vditor-preview) {
  background: var(--yuque-paper-bg);
}
</style>
