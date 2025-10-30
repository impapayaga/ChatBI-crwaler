import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter
from pathlib import Path
import aiofiles

class ErrorMonitor:
    """
    错误监控和统计系统
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.error_stats = defaultdict(int)
        self.error_trends = defaultdict(list)
        self.last_update = datetime.now()
    
    async def analyze_error_logs(self, hours: int = 24) -> Dict:
        """
        分析错误日志，生成统计报告
        
        Args:
            hours: 分析最近几小时的日志
            
        Returns:
            错误统计报告
        """
        error_log_file = self.log_dir / "errors.log"
        
        if not error_log_file.exists():
            return {"message": "没有找到错误日志文件"}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        error_counts = Counter()
        error_types = Counter()
        endpoints = Counter()
        hourly_stats = defaultdict(int)
        
        try:
            async with aiofiles.open(error_log_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        # 解析日志行
                        parts = line.split(' - ', 3)
                        if len(parts) < 4:
                            continue
                        
                        timestamp_str = parts[0]
                        log_data = parts[3]
                        
                        # 解析时间戳
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if timestamp < cutoff_time:
                            continue
                        
                        # 解析JSON数据
                        if log_data.startswith('{'):
                            error_info = json.loads(log_data)
                            
                            error_type = error_info.get('error_type', 'unknown')
                            endpoint = error_info.get('endpoint', 'unknown')
                            
                            error_counts[error_type] += 1
                            error_types[error_type] += 1
                            endpoints[endpoint] += 1
                            
                            # 按小时统计
                            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                            hourly_stats[hour_key] += 1
                    
                    except (json.JSONDecodeError, ValueError) as e:
                        continue
        
        except Exception as e:
            return {"error": f"分析日志时出错: {str(e)}"}
        
        return {
            "analysis_period": f"最近 {hours} 小时",
            "total_errors": sum(error_counts.values()),
            "error_types": dict(error_types.most_common()),
            "top_endpoints": dict(endpoints.most_common(10)),
            "hourly_distribution": dict(hourly_stats),
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_error_trends(self, days: int = 7) -> Dict:
        """
        获取错误趋势分析
        
        Args:
            days: 分析最近几天的趋势
            
        Returns:
            错误趋势报告
        """
        error_log_file = self.log_dir / "errors.log"
        
        if not error_log_file.exists():
            return {"message": "没有找到错误日志文件"}
        
        cutoff_time = datetime.now() - timedelta(days=days)
        daily_stats = defaultdict(lambda: defaultdict(int))
        
        try:
            async with aiofiles.open(error_log_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        parts = line.split(' - ', 3)
                        if len(parts) < 4:
                            continue
                        
                        timestamp_str = parts[0]
                        log_data = parts[3]
                        
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if timestamp < cutoff_time:
                            continue
                        
                        if log_data.startswith('{'):
                            error_info = json.loads(log_data)
                            error_type = error_info.get('error_type', 'unknown')
                            
                            day_key = timestamp.strftime('%Y-%m-%d')
                            daily_stats[day_key][error_type] += 1
                    
                    except (json.JSONDecodeError, ValueError):
                        continue
        
        except Exception as e:
            return {"error": f"分析趋势时出错: {str(e)}"}
        
        return {
            "analysis_period": f"最近 {days} 天",
            "daily_trends": dict(daily_stats),
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_performance_stats(self, hours: int = 24) -> Dict:
        """
        获取性能统计信息
        
        Args:
            hours: 分析最近几小时的性能数据
            
        Returns:
            性能统计报告
        """
        performance_log_file = self.log_dir / "performance.log"
        
        if not performance_log_file.exists():
            return {"message": "没有找到性能日志文件"}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        operation_stats = defaultdict(list)
        
        try:
            async with aiofiles.open(performance_log_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        parts = line.split(' - ', 3)
                        if len(parts) < 4:
                            continue
                        
                        timestamp_str = parts[0]
                        log_data = parts[3]
                        
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if timestamp < cutoff_time:
                            continue
                        
                        if log_data.startswith('{'):
                            perf_info = json.loads(log_data)
                            operation = perf_info.get('operation', 'unknown')
                            duration = perf_info.get('duration', 0)
                            
                            operation_stats[operation].append(duration)
                    
                    except (json.JSONDecodeError, ValueError):
                        continue
        
        except Exception as e:
            return {"error": f"分析性能时出错: {str(e)}"}
        
        # 计算统计指标
        stats_summary = {}
        for operation, durations in operation_stats.items():
            if durations:
                stats_summary[operation] = {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "total_duration": sum(durations)
                }
        
        return {
            "analysis_period": f"最近 {hours} 小时",
            "operation_stats": stats_summary,
            "generated_at": datetime.now().isoformat()
        }

# 全局监控实例
error_monitor = ErrorMonitor()