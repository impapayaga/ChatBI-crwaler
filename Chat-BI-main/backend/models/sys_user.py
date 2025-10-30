from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from models.base import Base


class SysUser(Base):
    """系统用户表"""
    __tablename__ = 'sys_user'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = Column(String(50), unique=True, nullable=False, index=True, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, index=True, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    full_name = Column(String(100), comment='全名')
    avatar_url = Column(String(500), comment='头像URL')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否激活')
    is_superuser = Column(Boolean, default=False, nullable=False, comment='是否超级管理员')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')

    def __repr__(self):
        return f"<SysUser(id={self.id}, username='{self.username}', email='{self.email}')>"
