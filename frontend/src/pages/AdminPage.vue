<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '~/stores/auth'
import { getNotes, createNote, updateNote, deleteNote, getCategories } from '~/api/notes'
import type { Note, TreeNode } from '~/types/note'
import { NButton, NModal, NInput, NDataTable, NSpace, NSelect, NPopconfirm, useMessage } from 'naive-ui'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()

const notes = ref<Note[]>([])
const tree = ref<TreeNode[]>([])
const loading = ref(false)
const showModal = ref(false)
const editNote = ref<Note | null>(null)
const formTitle = ref('')
const formContent = ref('')
const formType = ref<'article' | 'folder'>('article')
const formParentId = ref<number>(0)
const formStatus = ref<'published' | 'draft'>('published')
const formSlug = ref('')

async function load() {
  loading.value = true
  try {
    const [res, t] = await Promise.all([getNotes({ page_size: 500 }), getCategories()])
    notes.value = res.data.items
    tree.value = t.data || []
  } finally { loading.value = false }
}

function openCreate(type: 'article' | 'folder' = 'article') {
  editNote.value = null
  formTitle.value = ''; formContent.value = ''; formSlug.value = ''
  formType.value = type; formParentId.value = 0; formStatus.value = 'published'
  showModal.value = true
}

function openEdit(note: Note) {
  editNote.value = note
  formTitle.value = note.title; formContent.value = note.content || ''
  formSlug.value = note.slug || ''
  formType.value = note.type; formParentId.value = note.parent_id; formStatus.value = note.status
  showModal.value = true
}

async function handleSave() {
  if (!formTitle.value) { message.warning('请输入标题'); return }
  try {
    const data: any = { title: formTitle.value, content: formContent.value, slug: formSlug.value || undefined, type: formType.value, parent_id: formParentId.value, status: formStatus.value }
    if (editNote.value) {
      await updateNote(editNote.value.id, data)
      message.success('更新成功')
    } else {
      await createNote(data)
      message.success('创建成功')
    }
    showModal.value = false
    await load()
  } catch (e: any) { message.error(e?.msg || '操作失败') }
}

async function handleDelete(id: number) {
  try { await deleteNote(id); message.success('已删除'); await load() }
  catch (e: any) { message.error(e?.msg || '删除失败') }
}

onMounted(load)

const columns = [
  { title: 'ID', key: 'id', width: 60, sorter: true },
  { title: '类型', key: 'type', width: 70, render: (r: any) => r.type === 'folder' ? '📁' : '📄' },
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  { title: '状态', key: 'status', width: 80, render: (r: any) => r.status === 'published' ? '已发布' : '草稿' },
  { title: '版本', key: 'updated_at', width: 110, render: (r: any) => new Date(r.updated_at).toLocaleDateString() },
  {
    title: '操作', key: 'actions', width: 160,
    render: (row: any) => {
      return h(NSpace, null, {
        default: () => [
          h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
            trigger: () => h(NButton, { size: 'tiny', type: 'error' }, { default: () => '删除' }),
            default: () => '确定删除？',
          }),
        ],
      })
    }
  },
]
</script>

<template>
  <div class="min-h-screen bg-[#f4f5f5] dark:bg-[#2a2b30]">
    <header class="h-14 bg-white dark:bg-[#2c2d32] border-b border-[#e7e9e8] dark:border-[#383940] flex items-center px-5 gap-4">
      <RouterLink to="/" class="text-lg font-semibold text-main no-underline!">管理后台</RouterLink>
      <div class="flex-1" />
      <RouterLink to="/" class="link-brand! text-sm">前台</RouterLink>
      <button class="text-sm text-secondary border-none bg-transparent cursor-pointer" @click="auth.logout()">退出</button>
    </header>

    <div class="max-w-[1200px] mx-auto p-6">
      <div class="flex items-center gap-3 mb-4">
        <h1 class="text-xl font-bold text-main m-0">笔记管理</h1>
        <div class="flex-1" />
        <NButton type="primary" @click="openCreate('article')">+ 新建文章</NButton>
        <NButton @click="openCreate('folder')">+ 新建目录</NButton>
      </div>

      <div class="paper! p-4">
        <NDataTable :columns="columns" :data="notes" :loading="loading" :pagination="{ pageSize: 20 }" size="small" />
      </div>
    </div>

    <NModal v-model:show="showModal" title="编辑笔记" style="width: 800px;">
      <div class="flex flex-col gap-3 p-2">
        <NInput v-model:value="formTitle" placeholder="标题" size="large" />
        <NInput v-model:value="formSlug" placeholder="URL 标识（可选）" />
        <NSelect v-model:value="formType" :options="[{ label: '文章', value: 'article' }, { label: '目录', value: 'folder' }]" />
        <NSelect v-model:value="formStatus" v-if="formType === 'article'" :options="[{ label: '已发布', value: 'published' }, { label: '草稿', value: 'draft' }]" />
        <NSelect v-model:value="formParentId" :options="[{ label: '顶级（无父目录）', value: 0 }, ...tree.map((t: any) => ({ label: t.name, value: t.id, key: 'f-' + t.id }))]" placeholder="父目录" />
        <textarea v-model="formContent" placeholder="Markdown 内容" class="w-full h-60 p-3 rounded-md border border-[#e7e9e8] dark:border-[#383940] bg-white dark:bg-[#2e2f35] text-main font-mono text-13px resize-y outline-none" />
        <NButton type="primary" @click="handleSave">{{ editNote ? '保存' : '创建' }}</NButton>
      </div>
    </NModal>
  </div>
</template>
