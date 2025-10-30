"""
数据集相关模型
用于存储用户上传的CSV/Excel文件元数据
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from models.base import Base


class SysDataset(Base):
    """用户上传数据集表"""
    __tablename__ = 'sys_dataset'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment='数据集ID')
    user_id = Column(Integer, nullable=True, comment='上传用户ID')
    name = Column(String(255), nullable=False, comment='文件名')
    logical_name = Column(String(255), comment='逻辑名称(用户自定义)')
    description = Column(Text, comment='数据集描述')

    # 文件路径
    original_file_path = Column(Text, comment='MinIO原始文件路径')
    parsed_path = Column(Text, comment='Parquet文件路径')
    file_md5 = Column(String(32), index=True, comment='文件MD5哈希值,用于去重')

    # 统计信息
    row_count = Column(BigInteger, default=0, comment='行数')
    column_count = Column(Integer, default=0, comment='列数')
    file_size = Column(BigInteger, comment='文件大小(bytes)')

    # 解析状态
    parse_status = Column(
        String(50),
        default='pending',
        comment='解析状态: pending/parsing/parsed/failed'
    )
    parse_progress = Column(Integer, default=0, comment='解析进度(0-100)')
    error_message = Column(Text, comment='错误信息')

    # 数据分片状态
    chunk_status = Column(
        String(50),
        default='pending',
        comment='分片状态: pending/chunking/completed/failed'
    )
    chunk_progress = Column(Integer, default=0, comment='分片进度(0-100)')
    chunk_error = Column(Text, comment='分片错误信息')

    # 向量化状态
    vectorize_status = Column(
        String(50),
        default='pending',
        comment='向量化状态: pending/vectorizing/completed/failed'
    )
    vectorize_progress = Column(Integer, default=0, comment='向量化进度(0-100)')
    vectorize_error = Column(Text, comment='向量化错误信息')

    # (保留旧字段，向后兼容)
    embedding_status = Column(
        String(50),
        default='pending',
        comment='[已废弃] Embedding状态: pending/embedding/completed/failed'
    )
    embedding_progress = Column(Integer, default=0, comment='[已废弃] Embedding进度(0-100)')
    embedding_error = Column(Text, comment='[已废弃] Embedding错误信息')

    # 额外元数据
    extra_metadata = Column(JSONB, comment='额外元数据(JSON格式)')

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')

    def __repr__(self):
        return f"<SysDataset(id={self.id}, name='{self.name}', status='{self.parse_status}')>"


class SysDatasetColumn(Base):
    """数据集列信息表"""
    __tablename__ = 'sys_dataset_column'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='列ID')
    dataset_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment='数据集ID')

    # 列基本信息
    col_name = Column(String(255), nullable=False, comment='列名')
    col_index = Column(Integer, comment='列索引(0-based)')
    col_type = Column(String(50), comment='推断类型: int/float/string/date/bool')

    # 统计信息
    stats = Column(JSONB, comment='统计信息: {min, max, unique_count, null_count, mean, std}')
    sample_values = Column(JSONB, comment='示例值(前5个)')

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='创建时间')

    def __repr__(self):
        return f"<SysDatasetColumn(dataset_id={self.dataset_id}, col_name='{self.col_name}', type='{self.col_type}')>"


class SysDatasetAction(Base):
    """数据集查询动作记录表"""
    __tablename__ = 'sys_dataset_action'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='动作ID')
    dataset_id = Column(UUID(as_uuid=True), nullable=True, index=True, comment='数据集ID')
    user_id = Column(Integer, nullable=True, comment='用户ID')
    session_id = Column(String(255), comment='会话ID')

    # 输入输出
    input_text = Column(Text, nullable=False, comment='用户输入问题')
    intent = Column(String(50), comment='意图: chitchat/query/visualization')
    generated_sql = Column(Text, comment='生成的SQL')
    generated_spec = Column(JSONB, comment='生成的图表配置')

    # 结果
    result_preview = Column(JSONB, comment='结果预览数据')
    execution_time = Column(Integer, comment='执行时间(ms)')
    is_success = Column(Boolean, default=True, comment='是否成功')
    error_message = Column(Text, comment='错误信息')

    # 时间戳
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment='执行时间')

    def __repr__(self):
        return f"<SysDatasetAction(id={self.id}, intent='{self.intent}', success={self.is_success})>"
