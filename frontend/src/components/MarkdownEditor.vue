<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import Vditor from 'vditor'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const containerRef = ref<HTMLElement | null>(null)
let vditor: Vditor | null = null

onMounted(() => {
  if (!containerRef.value) return
  vditor = new Vditor(containerRef.value, {
    value: props.modelValue,
    mode: 'sv',           // 分屏：编辑 + 预览
    height: 480,
    placeholder: '输入 Markdown 内容...',
    toolbar: [
      'headings', 'bold', 'italic', 'strike', '|',
      'line', 'quote', 'list', 'ordered-list', 'check', 'code', 'inline-code', '|',
      'upload', 'link', 'table', '|',
      'undo', 'redo', '|',
      'fullscreen', 'outline',
    ],
    toolbarConfig: {
      pin: true,
    },
    counter: { enable: true, type: 'text' },
    preview: {
      mode: 'both',
      hljs: { style: 'github' },
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
/* Vditor 工具栏适配语雀风格 */
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
:deep(.vditor-toolbar__item--current) {
  background: var(--yuque-brand-soft);
  color: var(--yuque-brand);
}
/* 编辑区域样式 */
:deep(.vditor-input) {
  background: var(--yuque-paper-bg);
  color: var(--yuque-text);
}
:deep(.vditor-preview) {
  background: var(--yuque-paper-bg);
}
/* 预览区适配深色模式 */
:deep(.vditor-reset) {
  color: var(--yuque-text);
  font-size: 14px;
  line-height: 1.7;
  padding: 12px;
}
</style>
