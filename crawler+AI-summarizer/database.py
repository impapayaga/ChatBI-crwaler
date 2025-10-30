from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 数据库配置
DATABASE_URL = "sqlite:///./policy_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 政策文件表
class PolicyFile(Base):
    __tablename__ = "policy_files"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)  # 政策文件名称
    source = Column(String(100), nullable=False)  # 来源网站（北京/广东）
    url = Column(String(1000), nullable=False)  # 原始链接
    publish_date = Column(String(50))  # 发布日期
    publish_unit = Column(String(200))  # 发布单位
    content = Column(Text)  # 政策内容
    keywords_found = Column(String(200))  # 匹配的关键词
    created_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)  # 是否已处理

# AI总结表
class AISummary(Base):
    __tablename__ = "ai_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, nullable=False)  # 关联政策文件ID
    title = Column(String(500), nullable=False)  # 政策文件名称
    publish_unit = Column(String(200))  # 发布单位
    publish_date = Column(String(50))  # 发布日期
    summary = Column(Text, nullable=False)  # 政策摘要内容总结
    url = Column(String(1000), nullable=False)  # 超链接网址
    created_at = Column(DateTime, default=datetime.utcnow)

# 爬取配置表
class CrawlConfig(Base):
    __tablename__ = "crawl_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    website_name = Column(String(100), nullable=False)  # 网站名称
    website_url = Column(String(500), nullable=False)  # 网站URL
    keywords = Column(String(200), nullable=False)  # 关键词
    is_active = Column(Boolean, default=True)  # 是否启用
    last_crawl = Column(DateTime)  # 最后爬取时间
    created_at = Column(DateTime, default=datetime.utcnow)

# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化配置数据
def init_config():
    db = SessionLocal()
    try:
        # 检查是否已有配置
        if db.query(CrawlConfig).count() == 0:
            # 添加北京配置
            beijing_config = CrawlConfig(
                website_name="北京市政府",
                website_url="https://www.beijing.gov.cn/zhengce/zhengcefagui/",
                keywords="人工智能,医疗器械,生物医药"
            )
            # 添加广东配置
            guangdong_config = CrawlConfig(
                website_name="广东省政府",
                website_url="https://www.gd.gov.cn/zwgk/wjk/qbwj/index.html",
                keywords="人工智能,医疗器械,生物医药"
            )
            db.add(beijing_config)
            db.add(guangdong_config)
            db.commit()
    finally:
        db.close()

