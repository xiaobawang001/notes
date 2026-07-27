import api from './client'

export interface SettingsStatus {
  coze_token: string
  coze_base_url: string
  coze_users_database_id: string
  coze_notes_database_id: string
  coze_settings_database_id: string
  connection_ok: boolean
}

export interface SettingsUpdatePayload {
  coze_token: string
  coze_base_url: string
  coze_users_database_id: string
  coze_notes_database_id: string
  coze_settings_database_id: string
}

export function getSettings(): Promise<{ data: SettingsStatus }> {
  return api.get('/settings')
}

export function updateSettings(data: SettingsUpdatePayload): Promise<{ data: { msg: string } }> {
  return api.put('/settings', data)
}

export function testConnection(data: { coze_token: string; coze_base_url: string; coze_users_database_id: string }): Promise<{ data: { success: boolean; message: string } }> {
  return api.post('/settings/test-connection', data)
}
