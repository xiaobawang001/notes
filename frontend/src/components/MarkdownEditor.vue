<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const previewHtml = computed(() => {
  try {
    return marked.parse(props.modelValue || '') as string
  } catch {
    return '<p style="color:#999">渲染失败</p>'
  }
})
</script>

<template>
  <div class="editor-wrapper">
    <!-- 编辑区 -->
    <div class="editor-pane">
      <div class="pane-header">编辑</div>
      <textarea
        :value="modelValue"
        @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
        placeholder="Markdown 内容..."
        class="editor-textarea"
      />
    </div>
    <!-- 预览区 -->
    <div class="preview-pane">
      <div class="pane-header">预览</div>
      <div class="preview-body markdown-body" v-html="previewHtml" />
    </div>
  </div>
</template>

<style scoped>
.editor-wrapper {
  display: flex;
  gap: 1px;
  border: 1px solid var(--yuque-border);
  border-radius: 6px;
  overflow: hidden;
  background: var(--yuque-border);
  min-height: 320px;
}
.editor-pane,
.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--yuque-paper-bg);
}
.pane-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--yuque-text-secondary);
  padding: 6px 10px;
  border-bottom: 1px solid var(--yuque-border-light);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--yuque-page-bg);
}
.editor-textarea {
  flex: 1;
  min-height: 280px;
  padding: 12px;
  border: none;
  outline: none;
  resize: vertical;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--yuque-text);
  background: var(--yuque-paper-bg);
}
.preview-body {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.7;
  color: var(--yuque-text);
}
.preview-body :deep(h1) { font-size: 1.5em; margin: 0.5em 0; }
.preview-body :deep(h2) { font-size: 1.3em; margin: 0.5em 0; }
.preview-body :deep(h3) { font-size: 1.15em; margin: 0.5em 0; }
.preview-body :deep(p) { margin: 0.5em 0; }
.preview-body :deep(code) {
  background: var(--yuque-brand-soft);
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 0.9em;
}
.preview-body :deep(pre) {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
.preview-body :deep(pre code) { background: none; padding: 0; }
.preview-body :deep(blockquote) {
  border-left: 3px solid var(--yuque-brand);
  padding-left: 12px;
  color: var(--yuque-text-secondary);
  margin: 0.5em 0;
}
.preview-body :deep(img) { max-width: 100%; border-radius: 4px; }
.preview-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}
.preview-body :deep(th), .preview-body :deep(td) {
  border: 1px solid var(--yuque-border);
  padding: 6px 10px;
  text-align: left;
}
.preview-body :deep(th) { background: var(--yuque-page-bg); font-weight: 600; }
.preview-body :deep(ul), .preview-body :deep(ol) { padding-left: 1.5em; margin: 0.5em 0; }
</style>
