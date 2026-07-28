<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { getNotes, createNote, updateNote, deleteNote, getCategories } from '~/api/notes'
import api, { setApiPrefix } from '~/api/client'
import type { Note } from '~/types/note'
import { NButton, NModal, NDataTable, NSpace, NSelect, NPopconfirm, NCard, NTag, useMessage } from 'naive-ui'
import MarkdownEditor from '~/components/MarkdownEditor.vue'

const auth = useAuthStore()
const message = useMessage()

// ── 笔记管理状态 ──
const notes = ref<Note[]>([])
const tree = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const editNote = ref<Note | null>(null)
const formTitle = ref('')
const formContent = ref('')
const formType = ref<'article' | 'folder'>('article')
const formParentId = ref<number>(0)
const formStatus = ref<'published' | 'draft'>('published')
const formSlug = ref('')

// ── 管理功能状态 ──
const adminLoading = ref(false)
const pgStatus = ref<{ ok: boolean; message: string } | null>(null)
const cozeStatus = ref<{ ok: boolean; message: string } | null>(null)
const syncResult = ref<any>(null)
const backendStatus = ref<any>(null)
const activeBackend = ref('postgres')

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

// ── 管理功能 ──

async function testPg() {
  adminLoading.value = true
  pgStatus.value = null
  try {
    const res = await api.post('/admin/test-pg')
    pgStatus.value = res.data
    message.success(res.data?.ok ? 'PG 连接正常' : 'PG 连接失败')
  } catch (e: any) {
    pgStatus.value = { ok: false, message: e?.msg || '请求失败' }
    message.error('PG 连接测试失败')
  } finally { adminLoading.value = false }
}

async function testCoze() {
  adminLoading.value = true
  cozeStatus.value = null
  try {
    const res = await api.post('/admin/test-coze')
    cozeStatus.value = res.data
    message.success(res.data?.ok ? 'Coze 连接正常' : 'Coze 连接失败')
  } catch (e: any) {
    cozeStatus.value = { ok: false, message: e?.msg || '请求失败' }
    message.error('Coze 连接测试失败')
  } finally { adminLoading.value = false }
}

async function doSync() {
  adminLoading.value = true
  syncResult.value = null
  try {
    const res = await api.post('/admin/sync')
    syncResult.value = res.data
    if (res.data?.has_changes) {
      message.success('同步完成，有数据变更')
    } else {
      message.info('数据一致，无需同步')
    }
  } catch (e: any) {
    message.error(e?.msg || '同步失败')
  } finally { adminLoading.value = false }
}

async function toggleBackend(backend: string) {
  adminLoading.value = true
  try {
    const res = await api.post('/admin/switch-backend', { backend })
    backendStatus.value = res.data
    const active = res.data?.active_backend || 'postgres'
    activeBackend.value = active
    setApiPrefix(active)
    message.success(`已切换至 ${active === 'postgres' ? 'PostgreSQL' : 'Coze'}`)
  } catch (e: any) {
    message.error(e?.msg || '切换失败')
  } finally { adminLoading.value = false }
}

async function loadBackendStatus() {
  try {
    const res = await api.get('/admin/status')
    backendStatus.value = res.data
    const active = res.data?.active_backend || 'postgres'
    activeBackend.value = active
    setApiPrefix(active)
  } catch { /* ignore */ }
}

onMounted(() => { load(); loadBackendStatus() })

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
  <div class="min-h-screen bg-[var(--yuque-page-bg)]">
    <div class="max-w-[1200px] mx-auto p-6">

      <!-- 系统管理面板 -->
      <NCard title="系统管理" class="mb-6!">
        <div class="grid grid-cols-2 gap-4">
          <!-- PostgreSQL -->
          <div class="p-4 rounded-lg bg-[#f0f9eb] dark:bg-[#1e2e1a]">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-sm">PostgreSQL 连接</span>
              <NTag :type="pgStatus?.ok ? 'success' : 'error'" size="small">
                {{ pgStatus ? (pgStatus.ok ? '正常' : '异常') : '未检测' }}
              </NTag>
            </div>
            <p v-if="pgStatus" class="text-12px text-secondary">{{ pgStatus.message }}</p>
            <NButton size="small" :loading="adminLoading" @click="testPg" class="mt-2">测试连接</NButton>
          </div>

          <!-- Coze -->
          <div class="p-4 rounded-lg bg-[#ecf5ff] dark:bg-[#1a2332]">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-sm">Coze API 连接</span>
              <NTag :type="cozeStatus?.ok ? 'success' : 'error'" size="small">
                {{ cozeStatus ? (cozeStatus.ok ? '正常' : '异常') : '未检测' }}
              </NTag>
            </div>
            <p v-if="cozeStatus" class="text-12px text-secondary">{{ cozeStatus.message }}</p>
            <NButton size="small" :loading="adminLoading" @click="testCoze" class="mt-2">测试连接</NButton>
          </div>

          <!-- 数据同步 -->
          <div class="p-4 rounded-lg bg-[#fef0f0] dark:bg-[#2e1e1e]">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-sm">数据同步（PG → Coze）</span>
            </div>
            <NButton type="warning" size="small" :loading="adminLoading" @click="doSync">执行同步</NButton>
            <div v-if="syncResult" class="mt-2 text-12px text-secondary">
              <div>用户: 总计{{ syncResult.users?.total }} 新增{{ syncResult.users?.inserted }} 更新{{ syncResult.users?.updated }} 删除{{ syncResult.users?.deleted }} 跳过{{ syncResult.users?.skipped }}</div>
              <div>笔记: 总计{{ syncResult.notes?.total }} 新增{{ syncResult.notes?.inserted }} 更新{{ syncResult.notes?.updated }} 删除{{ syncResult.notes?.deleted }} 跳过{{ syncResult.notes?.skipped }}</div>
              <NTag :type="syncResult?.has_changes ? 'warning' : 'success'" size="tiny" class="mt-1">
                {{ syncResult?.has_changes ? '有变更' : '无变更（数据一致）' }}
              </NTag>
            </div>
          </div>

          <!-- 后端切换 -->
          <div class="p-4 rounded-lg bg-[#f5f5f5] dark:bg-[#2a2a2a]">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-sm">主后端切换</span>
              <NTag type="info" size="small">{{ activeBackend === 'postgres' ? 'PostgreSQL' : 'Coze' }}</NTag>
            </div>
            <NSpace class="mt-2">
              <NButton size="small" :type="activeBackend === 'postgres' ? 'primary' : 'default'" @click="toggleBackend('postgres')">PostgreSQL</NButton>
              <NButton size="small" :type="activeBackend === 'coze' ? 'primary' : 'default'" @click="toggleBackend('coze')">Coze</NButton>
              <NButton size="small" @click="toggleBackend('null')">恢复默认</NButton>
            </NSpace>
          </div>
        </div>
      </NCard>

      <!-- 笔记管理 -->
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

    <!-- 笔记编辑 Modal -->
    <NModal v-model:show="showModal" title="编辑笔记" style="width: 960px;">
      <div class="flex flex-col gap-3 p-2">
        <NInput v-model:value="formTitle" placeholder="标题" size="large" />
        <NInput v-model:value="formSlug" placeholder="URL 标识（可选）" />
        <NSelect v-model:value="formType" :options="[{ label: '文章', value: 'article' }, { label: '目录', value: 'folder' }]" />
        <NSelect v-model:value="formStatus" v-if="formType === 'article'" :options="[{ label: '已发布', value: 'published' }, { label: '草稿', value: 'draft' }]" />
        <NSelect v-model:value="formParentId" :options="[{ label: '顶级（无父目录）', value: 0 }, ...tree.map((t: any) => ({ label: t.name, value: t.id, key: 'f-' + t.id }))]" placeholder="父目录" />
        <MarkdownEditor v-model="formContent" />
        <NButton type="primary" @click="handleSave">{{ editNote ? '保存' : '创建' }}</NButton>
      </div>
    </NModal>
  </div>
</template>
