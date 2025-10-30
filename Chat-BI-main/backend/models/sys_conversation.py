from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from models.base import Base
import enum


class MessageRoleEnum(str, enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SysConversation(Base):
    """对话会话表"""
    __tablename__ = 'sys_conversation'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='会话ID')
    user_id = Column(Integer, ForeignKey('sys_user.id', ondelete='CASCADE'), nullable=False, index=True, comment='用户ID')
    title = Column(String(200), comment='会话标题')
    summary = Column(Text, comment='会话摘要')
    message_count = Column(Integer, default=0, nullable=False, comment='消息数量')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    def __repr__(self):
        return f"<SysConversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


class SysConversationMessage(Base):
    """对话消息表"""
    __tablename__ = 'sys_conversation_message'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='消息ID')
    conversation_id = Column(Integer, ForeignKey('sys_conversation.id', ondelete='CASCADE'), nullable=False, index=True, comment='会话ID')
    role = Column(SQLEnum(MessageRoleEnum), nullable=False, comment='消息角色')
    content = Column(Text, nullable=False, comment='消息内容')
    chart_data = Column(Text, comment='图表数据(JSON字符串)')
    chart_type = Column(String(50), comment='图表类型(bar/line/pie/doughnut)')
    tokens_used = Column(Integer, comment='使用的token数量')
    response_time = Column(Integer, comment='响应时间(毫秒)')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='创建时间')

    def __repr__(self):
        return f"<SysConversationMessage(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"
