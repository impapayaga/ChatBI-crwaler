"""
ChatBI前端适配API
为ChatBI前端提供数据爬取管理功能的API适配层
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, PolicyFile, AISummary, CrawlConfig, create_tables, init_config
from crawler import PolicyCrawler
from ai_summarizer import AISummarizer
from scheduler import PolicyScheduler
from pydantic import BaseModel
from typing import List, Optional
import logging
import threading
import time
import schedule
from datetime import datetime, timedelta
import json
import re

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 关键词提取函数
def extract_keywords_from_text(text):
    """从文本中提取关键词"""
    if not text:
        return "政策文件"
    
    # 简化的关键词检测
    keywords = []
    
    # 检测人工智能相关
    if any(word in text for word in ['人工智能', 'AI', '机器学习', '深度学习', '神经网络']):
        keywords.append('人工智能')
    
    # 检测生物医药相关
    if any(word in text for word in ['生物医药', '生物技术', '医药', '医疗', '健康']):
        keywords.append('生物医药')
    
    # 检测新能源相关
    if any(word in text for word in ['新能源', '清洁能源', '太阳能', '风能', '储能']):
        keywords.append('新能源')
    
    # 检测数字经济相关
    if any(word in text for word in ['数字经济', '数字化转型', '数字化', '信息化']):
        keywords.append('数字经济')
    
    # 检测科技创新相关
    if any(word in text for word in ['科技创新', '技术创新', '研发', '创新']):
        keywords.append('科技创新')
    
    # 检测绿色发展相关
    if any(word in text for word in ['绿色发展', '环保', '可持续发展', '碳中和']):
        keywords.append('绿色发展')
    
    # 检测智能制造相关
    if any(word in text for word in ['智能制造', '工业4.0', '自动化', '机器人']):
        keywords.append('智能制造')
    
    # 检测金融科技相关
    if any(word in text for word in ['金融科技', '区块链', '数字货币', '支付']):
        keywords.append('金融科技')
    
    # 检测教育相关
    if any(word in text for word in ['教育', '人才培养', '人才引进', '人才政策']):
        keywords.append('教育')
    
    # 检测产业相关
    if any(word in text for word in ['产业', '产业集群', '产业链', '产业升级']):
        keywords.append('产业')
    
    # 检测投资相关
    if any(word in text for word in ['投资', '招商引资', '项目', '建设']):
        keywords.append('投资')
    
    # 如果找到关键词，返回前5个，用逗号分隔
    if keywords:
        return ', '.join(keywords[:5])
    else:
        return "政策文件"

app = FastAPI(title="ChatBI数据爬取管理适配API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
create_tables()
init_config()

# 全局变量存储调度器状态
scheduler_status = {
    "is_running": False,
    "schedule_type": None,
    "start_time": None,
    "last_run": None,
    "next_run": None,
    "thread": None
}

# 固定的两个数据源
FIXED_SOURCES = [
    {
        "id": "1",
        "name": "北京市政府",
        "url": "https://www.beijing.gov.cn/zhengce/zhengcefagui/",
        "description": "北京市政府政策文件",
        "crawl_rules": '{"selector": ".content", "fields": ["title", "date", "content"]}',
        "is_active": True,
        "last_crawl_time": None,
        "last_crawl_status": None,
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "2", 
        "name": "广东省政府",
        "url": "https://www.gd.gov.cn/zwgk/wjk/qbwj/index.html",
        "description": "广东省政府政策文件",
        "crawl_rules": '{"selector": ".content", "fields": ["title", "date", "content"]}',
        "is_active": True,
        "last_crawl_time": None,
        "last_crawl_status": None,
        "created_at": "2024-01-01T00:00:00Z"
    }
]

# 模拟的定时任务数据
MOCK_SCHEDULES = [
    {
        "id": "1",
        "source_id": "1",
        "cron_expression": "0 9 * * 1",  # 每周一上午9点
        "description": "每周一爬取北京政策",
        "is_enabled": True,
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "2",
        "source_id": "2", 
        "cron_expression": "0 9 * * 2",  # 每周二上午9点
        "description": "每周二爬取广东政策",
        "is_enabled": True,
        "created_at": "2024-01-01T00:00:00Z"
    }
]

# 模拟的爬取结果数据
MOCK_CRAWL_RESULTS = []

# Pydantic模型
class ScrapeSource(BaseModel):
    id: str
    name: str
    url: str
    description: Optional[str] = None
    crawl_rules: Optional[str] = None
    is_active: bool = True
    last_crawl_time: Optional[str] = None
    last_crawl_status: Optional[str] = None
    created_at: str

class Schedule(BaseModel):
    id: str
    source_id: str
    cron_expression: str
    description: Optional[str] = None
    is_enabled: bool = True
    created_at: str

class CrawlResult(BaseModel):
    id: str
    source_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    records_count: Optional[int] = None
    crawl_rules: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str

class SourceCreate(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    crawl_rules: Optional[str] = None
    is_active: bool = True

class ScheduleCreate(BaseModel):
    source_id: str
    cron_expression: str
    description: Optional[str] = None
    is_enabled: bool = True

class CrawlRequest(BaseModel):
    source_id: str

# ==================== 数据源管理API ====================

@app.get("/api/scraper/sources", response_model=List[ScrapeSource])
async def get_scrape_sources():
    """获取爬取源列表"""
    # 更新最后爬取时间
    for source in FIXED_SOURCES:
        if source["id"] == "1":  # 北京
            # 从数据库获取最后爬取时间
            try:
                with get_db() as db:
                    last_policy = db.query(PolicyFile).filter(
                        PolicyFile.source == "北京市政府"
                    ).order_by(PolicyFile.created_at.desc()).first()
                    if last_policy:
                        source["last_crawl_time"] = last_policy.created_at.isoformat()
                        source["last_crawl_status"] = "成功"
            except:
                pass
        elif source["id"] == "2":  # 广东
            try:
                with get_db() as db:
                    last_policy = db.query(PolicyFile).filter(
                        PolicyFile.source == "广东省政府"
                    ).order_by(PolicyFile.created_at.desc()).first()
                    if last_policy:
                        source["last_crawl_time"] = last_policy.created_at.isoformat()
                        source["last_crawl_status"] = "成功"
            except:
                pass
    
    return FIXED_SOURCES

@app.post("/api/scraper/source", response_model=dict)
async def create_scrape_source(source: SourceCreate):
    """创建爬取源 - 仅支持查看，不支持创建新源"""
    raise HTTPException(status_code=403, detail="系统仅支持预定义的数据源")

@app.put("/api/scraper/source/{source_id}", response_model=dict)
async def update_scrape_source(source_id: str, source: SourceCreate):
    """更新爬取源 - 仅支持查看，不支持修改"""
    raise HTTPException(status_code=403, detail="系统仅支持预定义的数据源")

@app.delete("/api/scraper/source/{source_id}", response_model=dict)
async def delete_scrape_source(source_id: str):
    """删除爬取源 - 仅支持查看，不支持删除"""
    raise HTTPException(status_code=403, detail="系统仅支持预定义的数据源")

@app.patch("/api/scraper/source/{source_id}/toggle", response_model=dict)
async def toggle_source_status(source_id: str):
    """切换数据源状态 - 仅支持查看，不支持修改"""
    raise HTTPException(status_code=403, detail="系统仅支持预定义的数据源")

# ==================== 定时任务管理API ====================

@app.get("/api/scraper/schedules", response_model=List[Schedule])
async def get_schedules():
    """获取定时任务列表"""
    return MOCK_SCHEDULES

@app.post("/api/scraper/schedule", response_model=dict)
async def create_schedule(schedule: ScheduleCreate):
    """创建定时任务 - 仅支持查看，不支持创建"""
    raise HTTPException(status_code=403, detail="系统仅支持预定义的定时任务")

@app.put("/api/scraper/schedule/{schedule_id}", response_model=dict)
async def update_schedule(schedule_id: str, schedule: ScheduleCreate):
    """更新定时任务 - 仅支持查看，不支持修改"""
    raise HTTPException(status_code=403, detail="系统仅支持预定义的定时任务")

@app.delete("/api/scraper/schedule/{schedule_id}", response_model=dict)
async def delete_schedule(schedule_id: str):
    """删除定时任务 - 仅支持查看，不支持删除"""
    raise HTTPException(status_code=403, detail="系统仅支持预定义的定时任务")

@app.patch("/api/scraper/schedule/{schedule_id}/toggle", response_model=dict)
async def toggle_schedule_status(schedule_id: str):
    """切换定时任务状态 - 模拟操作"""
    # 找到对应的定时任务
    schedule = next((s for s in MOCK_SCHEDULES if s["id"] == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    
    # 模拟切换状态
    schedule["is_enabled"] = not schedule["is_enabled"]
    
    return {
        "success": True,
        "message": f"定时任务已{'启用' if schedule['is_enabled'] else '暂停'}",
        "is_enabled": schedule["is_enabled"]
    }

# ==================== 爬取结果API ====================

@app.get("/api/scraper/results", response_model=List[CrawlResult])
async def get_crawl_results():
    """获取爬取结果列表"""
    results = []
    
    # 从数据库获取AI总结数据，转换为爬取结果格式
    try:
        db = next(get_db())
        
        # 获取AI总结数据
        ai_summaries = db.query(AISummary).order_by(AISummary.created_at.desc()).limit(20).all()
        
        # 转换为爬取结果格式
        for summary in ai_summaries:
            # 根据标题判断来源
            if "北京" in summary.title or "北京市" in summary.title:
                source_id = "1"
            elif "广东" in summary.title or "广东省" in summary.title:
                source_id = "2"
            else:
                source_id = "1"  # 默认北京
            
            results.append({
                "id": f"summary_{summary.id}",
                "source_id": source_id,
                "status": "成功",
                "start_time": summary.created_at.isoformat(),
                "end_time": summary.created_at.isoformat(),
                "records_count": 1,
                "crawl_rules": '{"selector": ".content", "fields": ["title", "date", "content"]}',
                "error_message": None,
                "created_at": summary.created_at.isoformat()
            })
                
    except Exception as e:
        logger.error(f"获取爬取结果失败: {e}")
        # 如果没有数据，返回模拟数据
        results = [
            {
                "id": "demo_1",
                "source_id": "1",
                "status": "成功",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "records_count": 5,
                "crawl_rules": '{"selector": ".content", "fields": ["title", "date", "content"]}',
                "error_message": None,
                "created_at": datetime.now().isoformat()
            }
        ]
    
    return results

@app.get("/api/scraper/result/{result_id}/data")
async def get_crawl_result_data(result_id: str):
    """获取爬取结果的具体数据"""
    try:
        # 解析结果ID
        if result_id.startswith("beijing_"):
            policy_id = result_id.replace("beijing_", "")
            source_id = "1"
            # 从数据库获取北京政策文件详情
            db = next(get_db())
            policy = db.query(PolicyFile).filter(PolicyFile.id == policy_id).first()
            if not policy:
                raise HTTPException(status_code=404, detail="政策文件不存在")

            # 从标题和内容中提取关键词
            keywords = extract_keywords_from_text(policy.title + " " + policy.content)

            return {
                "items": [{
                    "title": policy.title,
                    "source": policy.source,
                    "url": policy.url,
                    "publish_date": policy.publish_date,
                    "publish_unit": policy.publish_unit,
                    "keywords_found": keywords,
                    "content": policy.content[:500] + "..." if len(policy.content) > 500 else policy.content
                }]
            }
        elif result_id.startswith("guangdong_"):
            policy_id = result_id.replace("guangdong_", "")
            source_id = "2"
            # 从数据库获取广东政策文件详情
            db = next(get_db())
            policy = db.query(PolicyFile).filter(PolicyFile.id == policy_id).first()
            if not policy:
                raise HTTPException(status_code=404, detail="政策文件不存在")

            # 从标题和内容中提取关键词
            keywords = extract_keywords_from_text(policy.title + " " + policy.content)

            return {
                "items": [{
                    "title": policy.title,
                    "source": policy.source,
                    "url": policy.url,
                    "publish_date": policy.publish_date,
                    "publish_unit": policy.publish_unit,
                    "keywords_found": keywords,
                    "content": policy.content[:500] + "..." if len(policy.content) > 500 else policy.content
                }]
            }
        elif result_id.startswith("summary_"):
            # 处理AI总结数据
            summary_id = result_id.replace("summary_", "")

            # 从数据库获取AI总结详情
            db = next(get_db())
            summary = db.query(AISummary).filter(AISummary.id == summary_id).first()
            if not summary:
                raise HTTPException(status_code=404, detail="AI总结不存在")

            # 从标题和总结中提取关键词
            keywords = extract_keywords_from_text(summary.title + " " + summary.summary)

            return {
                "items": [{
                    "title": summary.title,
                    "source": "北京市政府" if "北京" in summary.title else "广东省政府",
                    "url": summary.url,
                    "publish_date": summary.publish_date,
                    "publish_unit": summary.publish_unit,
                    "keywords_found": keywords,
                    "content": summary.summary  # 这里显示AI总结的内容
                }]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取爬取数据失败: {e}")
        # 返回模拟数据作为fallback
        return {
            "items": [
                {
                    "title": "模拟数据",
                    "source": "模拟来源",
                    "url": "https://example.com",
                    "publish_date": "2025-01-20",
                    "publish_unit": "模拟单位",
                    "keywords_found": "模拟关键词",
                    "content": "这是模拟的数据内容"
                }
            ]
        }

# ==================== 手动触发爬取API ====================

@app.post("/api/scraper/crawl", response_model=dict)
async def trigger_manual_crawl(crawl_request: CrawlRequest, background_tasks: BackgroundTasks):
    """手动触发爬取任务"""
    source_id = crawl_request.source_id
    
    # 验证数据源
    if source_id not in ["1", "2"]:
        raise HTTPException(status_code=400, detail="不支持的数据源")
    
    # 获取数据源信息
    source = next((s for s in FIXED_SOURCES if s["id"] == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 在后台执行爬取任务
    background_tasks.add_task(execute_crawl_task, source_id, source["name"])
    
    return {
        "success": True,
        "message": f"已启动{source['name']}的爬取任务",
        "source_id": source_id,
        "source_name": source["name"]
    }

async def execute_crawl_task(source_id: str, source_name: str):
    """执行爬取任务"""
    try:
        logger.info(f"开始执行{source_name}爬取任务")
        
        # 创建爬虫实例
        crawler = PolicyCrawler()
        
        # 执行爬取
        if source_id == "1":  # 北京
            # 使用正确的数据库连接
            db = next(get_db())
            policies_count = crawler.crawl_beijing_policies(db, max_pages=5)
            logger.info(f"{source_name}爬取完成，新增 {policies_count} 条政策")
        elif source_id == "2":  # 广东
            # 使用正确的数据库连接
            db = next(get_db())
            policies_count = crawler.crawl_guangdong_policies(db, max_pages=5)
            logger.info(f"{source_name}爬取完成，新增 {policies_count} 条政策")
        else:
            logger.error(f"不支持的数据源: {source_id}")
            return
        
        # 可选：自动执行AI总结
        try:
            summarizer = AISummarizer()
            db = next(get_db())
            processed_count = summarizer.process_unprocessed_policies(db)
            db.commit()
            logger.info(f"AI总结完成，处理了 {processed_count} 条数据")
        except Exception as e:
            logger.error(f"AI总结失败: {e}")
            
    except Exception as e:
        logger.error(f"爬取任务执行失败: {e}")
        # 即使爬取失败，也记录一个失败的结果
        try:
            with get_db() as db:
                # 这里可以添加失败记录的逻辑
                pass
        except:
            pass

# ==================== 统计信息API ====================

@app.get("/api/scraper/stats")
async def get_scraper_stats():
    """获取爬取统计信息"""
    try:
        with get_db() as db:
            # 统计政策文件数量
            total_policies = db.query(PolicyFile).count()
            beijing_policies = db.query(PolicyFile).filter(
                PolicyFile.source == "北京市政府"
            ).count()
            guangdong_policies = db.query(PolicyFile).filter(
                PolicyFile.source == "广东省政府"
            ).count()
            
            # 统计AI总结数量
            total_summaries = db.query(AISummary).count()
            
            return {
                "total_sources": 2,
                "active_sources": 2,
                "total_policies": total_policies,
                "beijing_policies": beijing_policies,
                "guangdong_policies": guangdong_policies,
                "total_summaries": total_summaries,
                "scheduled_tasks": 2,
                "last_crawl_time": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {
            "total_sources": 2,
            "active_sources": 2,
            "total_policies": 0,
            "beijing_policies": 0,
            "guangdong_policies": 0,
            "total_summaries": 0,
            "scheduled_tasks": 2,
            "last_crawl_time": None
        }

# ==================== 健康检查API ====================

@app.get("/api/scraper/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ChatBI数据爬取管理适配API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
