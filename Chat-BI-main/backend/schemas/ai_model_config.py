from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional, Any
from datetime import datetime


class AIModelConfigBase(BaseModel):
    """AI模型配置基础模型"""
    model_config = ConfigDict(populate_by_name=True)

    config_name: str = Field(..., min_length=1, max_length=100, description="配置名称", alias="configName")
    provider: Optional[str] = Field(None, max_length=50, description="模型提供商")
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称", alias="modelName")
    model_type: str = Field(..., min_length=1, max_length=50, description="模型类型", alias="modelType")
    api_url: str = Field(..., min_length=1, max_length=500, description="API地址", alias="apiUrl")
    api_key: Optional[str] = Field(None, max_length=255, description="API密钥", alias="apiKey")
    model_params: Optional[dict[str, Any]] = Field(None, description="模型参数", alias="modelParams")
    temperature: Optional[str] = Field("0.7", max_length=10, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大token数", alias="maxTokens")
    description: Optional[str] = Field(None, description="配置描述")
    is_default: bool = Field(False, description="是否默认配置", alias="isDefault")
    is_active: bool = Field(True, description="是否启用", alias="isActive")


class AIModelConfigCreate(AIModelConfigBase):
    """创建AI模型配置的请求模型"""
    user_id: int = Field(..., ge=1, description="用户ID", alias="userId")


class AIModelConfigUpdate(BaseModel):
    """更新AI模型配置的请求模型"""
    model_config = ConfigDict(populate_by_name=True)

    config_name: Optional[str] = Field(None, min_length=1, max_length=100, description="配置名称", alias="configName")
    provider: Optional[str] = Field(None, max_length=50, description="模型提供商")
    model_name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称", alias="modelName")
    model_type: Optional[str] = Field(None, min_length=1, max_length=50, description="模型类型", alias="modelType")
    api_url: Optional[str] = Field(None, min_length=1, max_length=500, description="API地址", alias="apiUrl")
    api_key: Optional[str] = Field(None, max_length=255, description="API密钥", alias="apiKey")
    model_params: Optional[dict[str, Any]] = Field(None, description="模型参数", alias="modelParams")
    temperature: Optional[str] = Field(None, max_length=10, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大token数", alias="maxTokens")
    description: Optional[str] = Field(None, description="配置描述")
    is_default: Optional[bool] = Field(None, description="是否默认配置", alias="isDefault")
    is_active: Optional[bool] = Field(None, description="是否启用", alias="isActive")


class AIModelConfigResponse(AIModelConfigBase):
    """AI模型配置响应模型"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., description="配置ID")
    user_id: int = Field(..., description="用户ID", alias="userId")
    created_at: datetime = Field(..., description="创建时间", alias="createdAt")
    updated_at: datetime = Field(..., description="更新时间", alias="updatedAt")


class AIModelConfigList(BaseModel):
    """AI模型配置列表响应"""
    total: int = Field(..., description="总数量")
    items: list[AIModelConfigResponse] = Field(..., description="配置列表")
