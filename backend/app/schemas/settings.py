"""系统配置相关 Pydantic Schema"""
from pydantic import BaseModel, Field


class SettingsStatus(BaseModel):
    """当前配置状态响应（敏感字段脱敏）"""
    coze_token: str = Field(description="Coze Token（脱敏，仅显示前4后4字符）")
    coze_base_url: str = Field(description="Coze API 基础地址")
    coze_users_database_id: str = Field(description="users 表 database ID")
    coze_notes_database_id: str = Field(description="notes 表 database ID")
    coze_settings_database_id: str = Field(description="settings 表 database ID")
    connection_ok: bool = Field(description="当前凭据是否可正常连接 Coze API")


class SettingsUpdate(BaseModel):
    """配置更新请求"""
    coze_token: str = Field(..., min_length=1, description="Coze 个人访问令牌")
    coze_base_url: str = Field(default="https://api.coze.cn", description="Coze API 基础地址")
    coze_users_database_id: str = Field(default="", description="users 表 database ID")
    coze_notes_database_id: str = Field(default="", description="notes 表 database ID")
    coze_settings_database_id: str = Field(default="", description="settings 表 database ID")


class TestConnectionResponse(BaseModel):
    """连接测试响应"""
    success: bool = Field(description="连接是否成功")
    message: str = Field(description="测试结果说明")
