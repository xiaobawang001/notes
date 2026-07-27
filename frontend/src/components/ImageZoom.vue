<script setup lang="ts">
const props = defineProps<{ visible: boolean; src: string; alt: string }>()
const emit = defineEmits<{ 'update:visible': [boolean] }>()

function close() { emit('update:visible', false) }
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-99 bg-black/85 flex items-center justify-center cursor-zoom-out" @click="close">
      <img :src="src" :alt="alt" class="max-w-[90vw] max-h-[90vh] rounded-lg cursor-default" @click.stop />
    </div>
  </Teleport>
</template>
