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

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="政策文件爬取与AI总结API", version="1.0.0")

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

# Pydantic模型
class PolicyResponse(BaseModel):
    id: int
    title: str
    source: str
    url: str
    publish_date: Optional[str]
    publish_unit: Optional[str]
    keywords_found: Optional[str]
    content: Optional[str]
    created_at: str

class AISummaryResponse(BaseModel):
    id: int
    title: str
    publish_unit: Optional[str]
    publish_date: Optional[str]
    summary: str
    url: str
    created_at: str

class CrawlConfigResponse(BaseModel):
    id: int
    website_name: str
    website_url: str
    keywords: str
    is_active: bool
    last_crawl: Optional[str]

class SchedulerStatusResponse(BaseModel):
    is_running: bool
    schedule_type: Optional[str]
    start_time: Optional[str]
    last_run: Optional[str]
    next_run: Optional[str]

class SchedulerRequest(BaseModel):
    schedule_type: str  # "weekly", "daily", "hourly"

# API路由
@app.get("/")
async def root():
    return {"message": "政策文件爬取与AI总结API服务运行中"}

@app.get("/api/policies", response_model=List[PolicyResponse])
async def get_policies(
    source: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取政策文件列表"""
    query = db.query(PolicyFile)
    if source:
        query = query.filter(PolicyFile.source == source)
    
    policies = query.order_by(PolicyFile.created_at.desc()).limit(limit).all()
    return policies

@app.get("/api/policies/beijing", response_model=List[PolicyResponse])
async def get_beijing_policies(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取北京市政府政策文件"""
    policies = db.query(PolicyFile).filter(
        PolicyFile.source == "北京市政府"
    ).order_by(PolicyFile.created_at.desc()).limit(limit).all()
    return policies

@app.get("/api/policies/guangdong", response_model=List[PolicyResponse])
async def get_guangdong_policies(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取广东省政府政策文件"""
    policies = db.query(PolicyFile).filter(
        PolicyFile.source == "广东省政府"
    ).order_by(PolicyFile.created_at.desc()).limit(limit).all()
    return policies

@app.get("/api/summaries", response_model=List[AISummaryResponse])
async def get_summaries(
    source: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取AI总结列表"""
    query = db.query(AISummary)
    if source:
        # 通过关联查询获取指定来源的总结
        query = query.join(PolicyFile).filter(PolicyFile.source == source)
    
    summaries = query.order_by(AISummary.created_at.desc()).limit(limit).all()
    return summaries

@app.get("/api/summaries/beijing", response_model=List[AISummaryResponse])
async def get_beijing_summaries(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取北京市政府AI总结"""
    summaries = db.query(AISummary).join(PolicyFile).filter(
        PolicyFile.source == "北京市政府"
    ).order_by(AISummary.created_at.desc()).limit(limit).all()
    return summaries

@app.get("/api/summaries/guangdong", response_model=List[AISummaryResponse])
async def get_guangdong_summaries(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取广东省政府AI总结"""
    summaries = db.query(AISummary).join(PolicyFile).filter(
        PolicyFile.source == "广东省政府"
    ).order_by(AISummary.created_at.desc()).limit(limit).all()
    return summaries

@app.get("/api/configs", response_model=List[CrawlConfigResponse])
async def get_crawl_configs(db: Session = Depends(get_db)):
    """获取爬取配置"""
    configs = db.query(CrawlConfig).all()
    return configs

@app.post("/api/crawl")
async def start_crawl(db: Session = Depends(get_db)):
    """启动爬取任务"""
    try:
        crawler = PolicyCrawler()
        total_found = crawler.crawl_all_policies(db)
        
        return {
            "success": True,
            "message": f"爬取完成，新增 {total_found} 条政策文件",
            "total_found": total_found
        }
    except Exception as e:
        logger.error(f"爬取失败: {e}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")

@app.post("/api/summarize")
async def start_summarize(db: Session = Depends(get_db)):
    """启动AI总结任务"""
    try:
        summarizer = AISummarizer()
        processed_count = summarizer.process_unprocessed_policies(db)
        
        return {
            "success": True,
            "message": f"AI总结完成，新增 {processed_count} 条总结",
            "processed_count": processed_count
        }
    except Exception as e:
        logger.error(f"AI总结失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI总结失败: {str(e)}")

@app.post("/api/crawl-and-summarize")
async def crawl_and_summarize(db: Session = Depends(get_db)):
    """执行完整的爬取和总结流程"""
    try:
        # 1. 爬取政策文件
        crawler = PolicyCrawler()
        total_found = crawler.crawl_all_policies(db)
        
        # 2. AI总结
        summarizer = AISummarizer()
        processed_count = summarizer.process_unprocessed_policies(db)
        
        return {
            "success": True,
            "message": "完整流程执行完成",
            "policies_found": total_found,
            "summaries_created": processed_count
        }
    except Exception as e:
        logger.error(f"完整流程执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
    total_policies = db.query(PolicyFile).count()
    total_summaries = db.query(AISummary).count()
    beijing_policies = db.query(PolicyFile).filter(PolicyFile.source == "北京市政府").count()
    guangdong_policies = db.query(PolicyFile).filter(PolicyFile.source == "广东省政府").count()
    
    return {
        "total_policies": total_policies,
        "total_summaries": total_summaries,
        "beijing_policies": beijing_policies,
        "guangdong_policies": guangdong_policies
    }

# 定时任务相关API
def run_scheduler_task(schedule_type: str):
    """在后台线程中运行调度器"""
    global scheduler_status
    try:
        scheduler = PolicyScheduler()
        scheduler_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        scheduler.scheduled_crawl_and_summarize()
    except Exception as e:
        logger.error(f"调度器任务执行失败: {e}")
    finally:
        scheduler_status["is_running"] = False

@app.post("/api/scheduler/start")
async def start_scheduler(request: SchedulerRequest):
    """启动定时任务调度器"""
    global scheduler_status
    
    if scheduler_status["is_running"]:
        raise HTTPException(status_code=400, detail="调度器已在运行中")
    
    if request.schedule_type not in ["weekly", "daily", "hourly"]:
        raise HTTPException(status_code=400, detail="无效的调度类型，支持: weekly, daily, hourly")
    
    try:
        # 清除现有的调度任务
        schedule.clear()
        
        # 设置新的调度任务
        if request.schedule_type == "weekly":
            schedule.every().monday.at("09:00").do(run_scheduler_task, request.schedule_type)
        elif request.schedule_type == "daily":
            schedule.every().day.at("09:00").do(run_scheduler_task, request.schedule_type)
        elif request.schedule_type == "hourly":
            schedule.every(6).hours.do(run_scheduler_task, request.schedule_type)
        
        # 启动调度器线程
        def scheduler_worker():
            global scheduler_status
            scheduler_status["is_running"] = True
            scheduler_status["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            scheduler_status["schedule_type"] = request.schedule_type
            
            next_run = schedule.next_run()
            if next_run:
                scheduler_status["next_run"] = next_run.strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"调度器已启动，类型: {request.schedule_type}")
            try:
                while scheduler_status["is_running"]:
                    schedule.run_pending()
                    time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器运行错误: {e}")
            finally:
                scheduler_status["is_running"] = False
        
        thread = threading.Thread(target=scheduler_worker, daemon=True)
        thread.start()
        scheduler_status["thread"] = thread
        
        return {
            "success": True,
            "message": f"调度器已启动，类型: {request.schedule_type}",
            "schedule_type": request.schedule_type,
            "next_run": scheduler_status["next_run"]
        }
        
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动调度器失败: {str(e)}")

@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler_status
    
    if not scheduler_status["is_running"]:
        raise HTTPException(status_code=400, detail="调度器未在运行")
    
    try:
        # 停止调度器
        scheduler_status["is_running"] = False
        schedule.clear()
        
        # 等待线程结束
        if scheduler_status["thread"] and scheduler_status["thread"].is_alive():
            scheduler_status["thread"].join(timeout=5)
        
        scheduler_status["thread"] = None
        scheduler_status["schedule_type"] = None
        scheduler_status["next_run"] = None
        
        logger.info("调度器已停止")
        
        return {
            "success": True,
            "message": "调度器已停止"
        }
        
    except Exception as e:
        logger.error(f"停止调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止调度器失败: {str(e)}")

@app.get("/api/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """获取调度器状态"""
    global scheduler_status
    
    # 更新下次运行时间
    if scheduler_status["is_running"]:
        next_run = schedule.next_run()
        if next_run:
            scheduler_status["next_run"] = next_run.strftime("%Y-%m-%d %H:%M:%S")
    
    return SchedulerStatusResponse(
        is_running=scheduler_status["is_running"],
        schedule_type=scheduler_status["schedule_type"],
        start_time=scheduler_status["start_time"],
        last_run=scheduler_status["last_run"],
        next_run=scheduler_status["next_run"]
    )

@app.post("/api/scheduler/run-once")
async def run_scheduler_once(db: Session = Depends(get_db)):
    """立即执行一次调度器任务"""
    try:
        scheduler = PolicyScheduler()
        scheduler.scheduled_crawl_and_summarize()
        
        return {
            "success": True,
            "message": "调度器任务执行完成"
        }
    except Exception as e:
        logger.error(f"执行调度器任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
