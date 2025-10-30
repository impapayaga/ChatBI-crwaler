import schedule
import time
import logging
from datetime import datetime
from database import get_db, CrawlConfig
from crawler import PolicyCrawler
from ai_summarizer import AISummarizer
from sqlalchemy.orm import Session

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyScheduler:
    def __init__(self):
        self.crawler = PolicyCrawler()
        self.summarizer = AISummarizer()
    
    def scheduled_crawl_and_summarize(self):
        """定时爬取和总结任务"""
        logger.info("开始执行定时爬取和总结任务...")
        
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 1. 执行爬取
            logger.info("开始爬取政策文件...")
            total_found = self.crawler.crawl_all_policies(db)
            logger.info(f"爬取完成，新增 {total_found} 条政策文件")
            
            # 2. 执行AI总结
            logger.info("开始AI总结...")
            processed_count = self.summarizer.process_unprocessed_policies(db)
            logger.info(f"AI总结完成，新增 {processed_count} 条总结")
            
            # 3. 更新配置中的最后爬取时间
            configs = db.query(CrawlConfig).all()
            for config in configs:
                config.last_crawl = datetime.utcnow()
            db.commit()
            
            logger.info("定时任务执行完成")
            
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
        finally:
            db.close()
    
    def start_scheduler(self, schedule_type="weekly"):
        """启动定时任务"""
        logger.info("启动定时任务调度器...")
        
        if schedule_type == "weekly":
            # 设置每周执行一次（每周一上午9点）
            schedule.every().monday.at("09:00").do(self.scheduled_crawl_and_summarize)
            logger.info("定时任务已设置：每周一上午9点执行")
        elif schedule_type == "daily":
            # 每天执行（用于测试）
            schedule.every().day.at("09:00").do(self.scheduled_crawl_and_summarize)
            logger.info("定时任务已设置：每天上午9点执行")
        elif schedule_type == "hourly":
            # 每6小时执行一次（用于测试）
            schedule.every(6).hours.do(self.scheduled_crawl_and_summarize)
            logger.info("定时任务已设置：每6小时执行一次")
        else:
            # 默认每周执行
            schedule.every().monday.at("09:00").do(self.scheduled_crawl_and_summarize)
            logger.info("定时任务已设置：每周一上午9点执行")
        
        # 显示下次执行时间
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"下次执行时间：{next_run}")
        
        # 运行调度器
        logger.info("调度器开始运行，按 Ctrl+C 停止...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("调度器已停止")
    
    def run_once(self):
        """立即执行一次任务（用于测试）"""
        logger.info("立即执行一次爬取和总结任务...")
        self.scheduled_crawl_and_summarize()

if __name__ == "__main__":
    scheduler = PolicyScheduler()
    
    # 可以选择立即执行一次或启动定时任务
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run_once":
        scheduler.run_once()
    else:
        scheduler.start_scheduler()
