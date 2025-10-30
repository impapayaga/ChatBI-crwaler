from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from models.base import Base


class SysAiModelConfig(Base):
    """AI模型配置表"""
    __tablename__ = 'sys_ai_model_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='配置ID')
    user_id = Column(Integer, ForeignKey('sys_user.id', ondelete='CASCADE'), nullable=False, index=True, comment='用户ID')
    config_name = Column(String(100), nullable=False, comment='配置名称')
    provider = Column(String(50), comment='模型提供商(siliconflow/openai/deepseek/custom)')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    model_type = Column(String(50), nullable=False, comment='模型类型(chat/generate/embedding)')
    api_url = Column(String(500), nullable=False, comment='API地址')
    api_key = Column(String(255), comment='API密钥')
    model_params = Column(JSON, comment='模型参数(JSON格式)')
    temperature = Column(String(10), default='0.7', comment='温度参数')
    max_tokens = Column(Integer, comment='最大token数')
    description = Column(Text, comment='配置描述')
    is_default = Column(Boolean, default=False, nullable=False, comment='是否默认配置')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否启用')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    def __repr__(self):
        return f"<SysAiModelConfig(id={self.id}, config_name='{self.config_name}', model_name='{self.model_name}')>"
