<script setup lang="ts">
import type { TreeNode as TreeNodeType } from '~/types/note'
import { FolderOpen } from 'lucide-vue-next'

defineProps<{ node: TreeNodeType; level: number; activeId?: number | null }>()
</script>

<template>
  <div class="tree-node">
    <!-- 目录节点 -->
    <div
      v-if="node.type === 'folder'"
      class="tree-folder"
      :style="{ paddingLeft: level === 0 ? '0' : '12px' }"
    >
      <div class="flex items-center gap-1.5 py-1 px-2 rounded-md text-14px font-medium text-[var(--yuque-text-secondary)]">
        <FolderOpen :size="14" />
        <span>{{ node.name }}</span>
      </div>
      <div v-if="node.children" class="tree-children">
        <TreeNode v-for="child in node.children" :key="child.id" :node="child" :level="level + 1" :active-id="activeId" />
      </div>
    </div>
    <!-- 文章节点 -->
    <RouterLink
      v-else
      :to="`/article/${node.id}`"
      class="block py-1 px-2 rounded-md text-14px text-main no-underline! hover:bg-[var(--yuque-brand-soft)] transition-colors"
      :class="{ 'ml-3': level > 0, 'bg-[var(--yuque-brand-soft)] text-[var(--yuque-brand)]!': node.id === activeId }"
    >
      {{ node.name }}
    </RouterLink>
  </div>
</template>
