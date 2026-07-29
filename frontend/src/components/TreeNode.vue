<script setup lang="ts">
import { ref, inject, watch } from 'vue'
import type { TreeNode as TreeNodeType } from '~/types/note'
import { ChevronRight, FolderOpen } from 'lucide-vue-next'

const props = defineProps<{ node: TreeNodeType; level: number; activeId?: number | null; ancestorIds?: Set<number> }>()

const expanded = ref(props.level < 1) // 默认展开第一级
const expandAll = inject<boolean>('treeExpandAll', false)
const collapseAll = inject<boolean>('treeCollapseAll', false)
const locateTarget = inject<number>('treeLocateTarget', 0)
const locateAncestors = inject<Set<number>>('treeLocateAncestors', new Set())

watch(expandAll, (v) => { if (v) expanded.value = true })
watch(collapseAll, (v) => { if (v) expanded.value = false })

function toggle() { expanded.value = !expanded.value }

// 定位：展开祖先目录 + 滚动到目标文章
watch(locateTarget, (id) => {
  if (!id) return
  // 如果是目录且是目标祖先 → 展开自己
  if (props.node.type === 'folder' && locateAncestors.value.has(props.node.id)) {
    expanded.value = true
  }
  // 如果是文章且匹配目标 → 滚动到可视区域
  if (props.node.type !== 'folder' && id === props.node.id) {
    const el = document.querySelector(`[data-node-id="${id}"]`)
    if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
})
</script>

<template>
  <div class="tree-node">
    <!-- 目录节点 -->
    <div v-if="node.type === 'folder'">
      <div
        class="flex items-center gap-1 py-1 px-2 rounded-md text-14px cursor-pointer select-none transition-colors hover:bg-[rgba(0,185,107,0.1)]"
        :class="[
          level === 0 ? 'font-medium' : '',
          'text-[var(--yuque-text-secondary)]',
        ]"
        :style="{ paddingLeft: level > 0 ? `${level * 12}px` : '0' }"
        @click="toggle"
      >
        <ChevronRight
          :size="14"
          class="shrink-0 transition-transform duration-150"
          :class="{ 'rotate-90': expanded }"
        />
        <FolderOpen :size="14" class="shrink-0" />
        <span class="truncate">{{ node.name }}</span>
      </div>
      <div v-if="node.children && expanded" class="tree-children">
        <TreeNode v-for="child in node.children" :key="child.id" :node="child" :level="level + 1" :active-id="activeId" :ancestor-ids="ancestorIds" />
      </div>
    </div>

    <!-- 文章节点 -->
    <RouterLink
      v-else
      :to="`/article/${node.id}`"
      :data-node-id="node.id"
      class="block py-1 px-2 rounded-md text-14px text-main no-underline! transition-colors"
      :class="{
        'hover:bg-[rgba(0,185,107,0.1)]': node.id !== activeId,
        'bg-[rgba(0,185,107,0.2)] text-[var(--yuque-brand)]! font-semibold': node.id === activeId,
      }"
      :style="{ paddingLeft: level > 0 ? `${level * 12 + 24}px` : '24px' }"
    >
      <span class="truncate block">{{ node.name }}</span>
    </RouterLink>
  </div>
</template>
