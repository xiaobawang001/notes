<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '~/stores/auth'
import { getNotes, createNote, updateNote, deleteNote, getCategories } from '~/api/notes'
import { getSettings, updateSettings, testConnection } from '~/api/settings'
import type { Note, TreeNode } from '~/types/note'
import type { SettingsStatus } from '~/api/settings'
import { NButton, NModal, NInput, NDataTable, NSpace, NSelect, NPopconfirm, NTabs, NTabPane, NSpin, useMessage } from 'naive-ui'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()

// ── 笔记管理 ──
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

// ── 系统配置 ──
const activeTab = ref('notes')
const settingsLoading = ref(false)
const settingsSaving = ref(false)
const testing = ref(false)
const configStatus = ref<SettingsStatus | null>(null)

const configToken = ref('')
const configBaseUrl = ref('https://api.coze.cn')
const configUsersDbId = ref('')
const configNotesDbId = ref('')
const configSettingsDbId = ref('')

async function loadSettings() {
  settingsLoading.value = true
  try {
    const res = await getSettings()
    configStatus.value = res.data
    // 不自动回填完整 token（后端只返回脱敏值）
    configBaseUrl.value = res.data.coze_base_url
    configUsersDbId.value = res.data.coze_users_database_id
    configNotesDbId.value = res.data.coze_notes_database_id
    configSettingsDbId.value = res.data.coze_settings_database_id
  } catch (e: any) {
    message.error(e?.msg || '获取配置失败')
  } finally { settingsLoading.value = false }
}

async function handleTestConnection() {
  if (!configToken.value) { message.warning('请先输入 Coze Token'); return }
  testing.value = true
  try {
    const res = await testConnection({
      coze_token: configToken.value,
      coze_base_url: configBaseUrl.value,
      coze_users_database_id: configUsersDbId.value,
    })
    if (res.data.success) {
      message.success('连接成功！凭据有效')
    } else {
      message.error(res.data.message || '连接失败')
    }
  } catch (e: any) {
    message.error(e?.msg || '测试连接失败')
  } finally { testing.value = false }
}

async function handleSaveSettings() {
  if (!configToken.value) { message.warning('请输入 Coze Token'); return }
  settingsSaving.value = true
  try {
    await updateSettings({
      coze_token: configToken.value,
      coze_base_url: configBaseUrl.value,
      coze_users_database_id: configUsersDbId.value,
      coze_notes_database_id: configNotesDbId.value,
      coze_settings_database_id: configSettingsDbId.value,
    })
    message.success('配置已保存并生效')
    await loadSettings()
  } catch (e: any) {
    message.error(e?.msg || '保存配置失败')
  } finally { settingsSaving.value = false }
}

function onTabChange(tab: string) {
  if (tab === 'settings' && !configStatus.value) {
    loadSettings()
  }
}
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
      <!-- 顶部 Tab 切换 -->
      <NTabs v-model:value="activeTab" type="line" @update:value="onTabChange">
        <!-- ========== 笔记管理 Tab ========== -->
        <NTabPane name="notes" tab="笔记管理">
          <div class="flex items-center gap-3 mb-4 mt-2">
            <h1 class="text-xl font-bold text-main m-0">笔记管理</h1>
            <div class="flex-1" />
            <NButton type="primary" @click="openCreate('article')">+ 新建文章</NButton>
            <NButton @click="openCreate('folder')">+ 新建目录</NButton>
          </div>

          <div class="paper! p-4">
            <NDataTable :columns="columns" :data="notes" :loading="loading" :pagination="{ pageSize: 20 }" size="small" />
          </div>
        </NTabPane>

        <!-- ========== 系统配置 Tab ========== -->
        <NTabPane name="settings" tab="系统配置">
          <div class="mt-2">
            <h1 class="text-xl font-bold text-main mb-1">系统配置</h1>
            <p class="text-sm text-secondary mb-5">Coze API 密钥每月自动更新，管理员可在此重新配置凭据。</p>

            <NSpin :show="settingsLoading">
              <div class="paper! p-6 max-w-[640px]">
                <!-- 连接状态 -->
                <div class="flex items-center gap-2 mb-5 pb-4 border-b border-[#e7e9e8] dark:border-[#383940]">
                  <span class="text-sm text-secondary">当前连接状态：</span>
                  <span v-if="configStatus?.connection_ok" class="text-sm text-green-600 font-medium">● 已连接</span>
                  <span v-else class="text-sm text-red-500 font-medium">● 未连接</span>
                </div>

                <!-- Coze Token -->
                <div class="mb-4">
                  <label class="block text-sm font-medium text-main mb-1.5">
                    Coze Token
                    <span class="text-red-500 ml-0.5">*</span>
                  </label>
                  <NInput
                    v-model:value="configToken"
                    type="password"
                    show-password-on="click"
                    :placeholder="configStatus?.coze_token ? `当前: ${configStatus.coze_token}` : '请输入 Coze 个人访问令牌'"
                  />
                  <span class="text-xs text-secondary mt-1 block">
                    每月自动更新，从 Coze 控制台 → 个人访问令牌 获取
                  </span>
                </div>

                <!-- Coze Base URL -->
                <div class="mb-4">
                  <label class="block text-sm font-medium text-main mb-1.5">Coze API 地址</label>
                  <NInput v-model:value="configBaseUrl" placeholder="https://api.coze.cn" />
                </div>

                <!-- Users Database ID -->
                <div class="mb-4">
                  <label class="block text-sm font-medium text-main mb-1.5">Users 表 Database ID</label>
                  <NInput v-model:value="configUsersDbId" placeholder="users 表的数据库 ID" />
                </div>

                <!-- Notes Database ID -->
                <div class="mb-4">
                  <label class="block text-sm font-medium text-main mb-1.5">Notes 表 Database ID</label>
                  <NInput v-model:value="configNotesDbId" placeholder="notes 表的数据库 ID" />
                </div>

                <!-- Settings Database ID -->
                <div class="mb-5">
                  <label class="block text-sm font-medium text-main mb-1.5">Settings 表 Database ID</label>
                  <NInput v-model:value="configSettingsDbId" placeholder="settings 表的数据库 ID" />
                </div>

                <!-- 操作按钮 -->
                <div class="flex gap-3">
                  <NButton type="primary" :loading="settingsSaving" @click="handleSaveSettings">
                    保存配置
                  </NButton>
                  <NButton :loading="testing" @click="handleTestConnection">
                    测试连接
                  </NButton>
                </div>

                <!-- 提示 -->
                <div class="mt-5 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-md border border-amber-200 dark:border-amber-800">
                  <p class="text-xs text-amber-700 dark:text-amber-300 m-0">
                    注意：如果当前 Coze Token 已完全失效无法连接，请通过 Vercel Dashboard → Settings → Environment Variables 手动更新 COZE_TOKEN 环境变量，然后重新部署。
                  </p>
                </div>
              </div>
            </NSpin>
          </div>
        </NTabPane>
      </NTabs>
    </div>

    <!-- 笔记编辑 Modal -->
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
