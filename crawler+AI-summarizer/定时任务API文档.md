# 定时任务API文档

## 概述

定时任务API允许您通过HTTP请求来控制政策文件爬取和AI总结的定时任务。这些API提供了启动、停止、状态查询和立即执行等功能。

## API端点

### 1. 启动定时任务调度器

**POST** `/api/scheduler/start`

启动指定类型的定时任务调度器。

#### 请求体
```json
{
    "schedule_type": "weekly"  // 支持: "weekly", "daily", "hourly"
}
```

#### 响应
```json
{
    "success": true,
    "message": "调度器已启动，类型: weekly",
    "schedule_type": "weekly",
    "next_run": "2024-01-15 09:00:00"
}
```

#### 调度类型说明
- **weekly**: 每周一上午9点执行
- **daily**: 每天上午9点执行  
- **hourly**: 每6小时执行一次

### 2. 停止定时任务调度器

**POST** `/api/scheduler/stop`

停止当前运行的定时任务调度器。

#### 响应
```json
{
    "success": true,
    "message": "调度器已停止"
}
```

### 3. 获取调度器状态

**GET** `/api/scheduler/status`

获取当前调度器的运行状态。

#### 响应
```json
{
    "is_running": true,
    "schedule_type": "weekly",
    "start_time": "2024-01-08 10:30:00",
    "last_run": "2024-01-08 09:00:00",
    "next_run": "2024-01-15 09:00:00"
}
```

#### 字段说明
- `is_running`: 是否正在运行
- `schedule_type`: 调度类型
- `start_time`: 启动时间
- `last_run`: 上次执行时间
- `next_run`: 下次执行时间

### 4. 立即执行一次任务

**POST** `/api/scheduler/run-once`

立即执行一次爬取和AI总结任务，不等待定时器。

#### 响应
```json
{
    "success": true,
    "message": "调度器任务执行完成"
}
```

## 使用示例

### JavaScript示例

```javascript
// 启动每周定时任务
async function startWeeklyScheduler() {
    const response = await fetch('http://localhost:8000/api/scheduler/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            schedule_type: 'weekly'
        })
    });
    
    const result = await response.json();
    console.log(result);
}

// 获取调度器状态
async function getSchedulerStatus() {
    const response = await fetch('http://localhost:8000/api/scheduler/status');
    const status = await response.json();
    console.log(status);
}

// 停止调度器
async function stopScheduler() {
    const response = await fetch('http://localhost:8000/api/scheduler/stop', {
        method: 'POST'
    });
    
    const result = await response.json();
    console.log(result);
}

// 立即执行一次任务
async function runOnce() {
    const response = await fetch('http://localhost:8000/api/scheduler/run-once', {
        method: 'POST'
    });
    
    const result = await response.json();
    console.log(result);
}
```

### Python示例

```python
import requests

# 启动每日定时任务
def start_daily_scheduler():
    response = requests.post('http://localhost:8000/api/scheduler/start', 
                           json={'schedule_type': 'daily'})
    return response.json()

# 获取调度器状态
def get_scheduler_status():
    response = requests.get('http://localhost:8000/api/scheduler/status')
    return response.json()

# 停止调度器
def stop_scheduler():
    response = requests.post('http://localhost:8000/api/scheduler/stop')
    return response.json()

# 立即执行一次任务
def run_scheduler_once():
    response = requests.post('http://localhost:8000/api/scheduler/run-once')
    return response.json()
```

### cURL示例

```bash
# 启动每周定时任务
curl -X POST "http://localhost:8000/api/scheduler/start" \
     -H "Content-Type: application/json" \
     -d '{"schedule_type": "weekly"}'

# 获取调度器状态
curl -X GET "http://localhost:8000/api/scheduler/status"

# 停止调度器
curl -X POST "http://localhost:8000/api/scheduler/stop"

# 立即执行一次任务
curl -X POST "http://localhost:8000/api/scheduler/run-once"
```

## 错误处理

### 常见错误码

- **400 Bad Request**: 请求参数错误或调度器状态冲突
- **500 Internal Server Error**: 服务器内部错误

### 错误响应示例

```json
{
    "detail": "调度器已在运行中"
}
```

## 注意事项

1. **单实例运行**: 同时只能运行一个调度器实例
2. **线程安全**: 调度器在独立线程中运行，不会阻塞API服务
3. **自动清理**: 服务重启后调度器状态会重置
4. **日志记录**: 所有调度器操作都会记录到日志中

## 集成建议

### 前端集成
- 使用定时器定期查询调度器状态
- 提供启动/停止按钮和状态显示
- 显示下次执行时间

### 监控集成
- 监控调度器运行状态
- 设置告警机制
- 记录执行历史

### 自动化集成
- 结合CI/CD流程
- 与其他系统集成
- 实现故障恢复机制
