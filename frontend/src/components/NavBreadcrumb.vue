<script setup lang="ts">
defineProps<{ items: { label: string; to?: string }[] }>()
</script>

<template>
  <nav class="flex items-center gap-1 text-13px text-[#8a8f8d] dark:text-[#76777d] mb-4">
    <template v-for="(item, i) in items" :key="i">
      <template v-if="item.to">
        <RouterLink :to="item.to" class="link-brand!">{{ item.label }}</RouterLink>
      </template>
      <template v-else>
        <span>{{ item.label }}</span>
      </template>
      <span v-if="i < items.length - 1" class="mx-1">/</span>
    </template>
  </nav>
</template>
