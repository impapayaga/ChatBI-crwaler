#!/usr/bin/env python3
"""
政策文件爬取与AI总结系统主程序
"""

import uvicorn
import argparse
import logging
from database import create_tables, init_config
from scheduler import PolicyScheduler

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="政策文件爬取与AI总结系统")
    parser.add_argument("--mode", choices=["api", "scheduler", "run_once"], 
                       default="api", help="运行模式")
    parser.add_argument("--schedule", choices=["weekly", "daily", "hourly"], 
                       default="weekly", help="调度频率（仅用于scheduler模式）")
    parser.add_argument("--host", default="0.0.0.0", help="API服务主机")
    parser.add_argument("--port", type=int, default=8000, help="API服务端口")
    
    args = parser.parse_args()
    
    # 初始化数据库
    logger.info("初始化数据库...")
    create_tables()
    init_config()
    logger.info("数据库初始化完成")
    
    if args.mode == "api":
        # 启动API服务
        logger.info(f"启动API服务，地址: http://{args.host}:{args.port}")
        uvicorn.run("api:app", host=args.host, port=args.port, reload=True)
        
    elif args.mode == "scheduler":
        # 启动定时任务
        logger.info(f"启动定时任务调度器，调度频率: {args.schedule}")
        scheduler = PolicyScheduler()
        scheduler.start_scheduler(args.schedule)
        
    elif args.mode == "run_once":
        # 立即执行一次任务
        logger.info("立即执行一次爬取和总结任务...")
        scheduler = PolicyScheduler()
        scheduler.run_once()

if __name__ == "__main__":
    main()
