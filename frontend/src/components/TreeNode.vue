<script setup lang="ts">
import { ref, inject, watch, onMounted } from 'vue'
import type { TreeNode as TreeNodeType } from '~/types/note'
import { ChevronRight, FolderOpen } from 'lucide-vue-next'

const props = defineProps<{ node: TreeNodeType; level: number; activeId?: number | null }>()

const expanded = ref(props.level < 1) // 默认展开第一级
const expandAll = inject<boolean>('treeExpandAll', false)
const collapseAll = inject<boolean>('treeCollapseAll', false)

watch(expandAll, (v) => { if (v) expanded.value = true })
watch(collapseAll, (v) => { if (v) expanded.value = false })

function toggle() { expanded.value = !expanded.value }

// 定位当前文章：滚动到匹配节点
const elRef = ref<HTMLElement | null>(null)
const locateSignal = inject<number>('treeLocateId', 0)
watch(locateSignal, (id) => {
  if (id && id === props.node.id) {
    elRef.value?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
})
</script>

<template>
  <div class="tree-node" :ref="(el: any) => { if (node.id === activeId) elRef.value = el as HTMLElement }">
    <!-- 目录节点 -->
    <div v-if="node.type === 'folder'">
      <div
        class="flex items-center gap-1 py-1 px-2 rounded-md text-14px cursor-pointer select-none transition-colors hover:bg-[var(--yuque-brand-soft)]"
        :class="level === 0 ? 'font-medium text-[var(--yuque-text-secondary)]' : 'text-[var(--yuque-text-secondary)]'"
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
        <TreeNode v-for="child in node.children" :key="child.id" :node="child" :level="level + 1" :active-id="activeId" />
      </div>
    </div>

    <!-- 文章节点 -->
    <RouterLink
      v-else
      :to="`/article/${node.id}`"
      class="block py-1 px-2 rounded-md text-14px text-main no-underline! transition-colors"
      :class="{
        'hover:bg-[var(--yuque-brand-soft)]': node.id !== activeId,
        'bg-[var(--yuque-brand-soft)] text-[var(--yuque-brand)]! font-medium': node.id === activeId,
      }"
      :style="{ paddingLeft: level > 0 ? `${level * 12 + 24}px` : '24px' }"
    >
      <span class="truncate block">{{ node.name }}</span>
    </RouterLink>
  </div>
</template>
