# ChatBI + 爬虫数据管理系统

## 📋 项目概述

这是一个集成的商业智能(BI)分析平台，包含两个核心组件：

### 🎯 主项目 (Chat-BI-main)
- **ChatBI**: 基于AI的智能商业智能分析平台
- **技术栈**: Vue.js + FastAPI + PostgreSQL + Redis + MinIO + Qdrant
- **核心功能**: 自然语言问答、自动生成可视化图表、智能多数据集联合分析

### 🤖 数据爬取组件 (crawler+AI-summarizer)
- **政策文件智能分析系统**: 自动爬取政府政策文件，使用AI进行智能总结
- **技术栈**: Python + FastAPI + SQLite + AI API
- **核心功能**: 自动数据爬取、AI智能总结、定时调度任务

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ChatBI完整系统                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  ChatBI前端  │    │ ChatBI后端   │    │ Crawler后端  │     │
│  │  (Vue.js)    │    │ (FastAPI)   │    │ (FastAPI)   │     │
│  │  Port:3000   │◄──►│ Port:11434  │    │ Port:8001   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                基础设施服务                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│  │  │ PostgreSQL   │  │   Redis     │  │   MinIO     │    │ │
│  │  │ Port:5433    │  │ Port:6388   │  │ Port:9000   │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │ │
│  │  ┌─────────────┐                                      │ │
│  │  │   Qdrant     │                                      │ │
│  │  │ Port:6333    │                                      │ │
│  │  └─────────────┘                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 完整启动流程

### 环境准备

**必需环境**:
- ✅ Docker Desktop (用于运行基础设施服务)
- ✅ Node.js + pnpm (前端开发)
- ✅ Python + conda (后端开发)
- ✅ 所有Python依赖包

### 步骤1: 启动Docker基础设施服务

```bash
# 进入ChatBI后端目录
cd C:\Users\KC\Desktop\POC\Chat-BI-main\backend

# 启动Docker服务 (PostgreSQL, Redis, MinIO, Qdrant)
docker-compose up -d

# 检查服务状态 - 应该看到4个服务全部运行
docker-compose ps
```

**预期输出**:
- chatbi-postgres (PostgreSQL数据库)
- chatbi-redis (Redis缓存)
- chatbi-minio (MinIO对象存储)
- chatbi-qdrant (Qdrant向量数据库)

### 步骤2: 初始化数据库

```bash
# 进入ChatBI后端目录
cd C:\Users\KC\Desktop\POC\Chat-BI-main\backend

# 激活conda环境
conda activate chatbi

# 初始化数据库
python backend/init_db.py
```

### 步骤3: 启动ChatBI后端服务

```bash
# 进入ChatBI后端目录
cd C:\Users\KC\Desktop\POC\Chat-BI-main\backend

# 激活conda环境
conda activate chatbi

# 设置Python路径
$env:PYTHONPATH = "C:\Users\KC\Desktop\POC\Chat-BI-main\backend"

# 启动ChatBI后端服务
python main.py
```

**成功标志**: 看到 `✅ INFO: Uvicorn running on http://127.0.0.1:11434`

### 步骤4: 启动Crawler数据爬取服务

```bash
# 进入crawler项目目录
cd C:\Users\KC\Desktop\POC\crawler+AI-summarizer

# 安装依赖 (如果未安装)
pip install -r requirements.txt

# 启动适配API服务
python adapter_api.py
```

**成功标志**: 看到 `✅ INFO: Uvicorn running on http://0.0.0.0:8001`

### 步骤5: 启动ChatBI前端服务

```bash
# 新开一个终端，进入ChatBI前端目录
cd C:\Users\KC\Desktop\POC\Chat-BI-main\frontend

# 启动前端开发服务器
pnpm dev
```

**成功标志**: 看到前端编译完成，可访问 http://localhost:3000

## 🔧 环境配置

### ChatBI前端配置 (.env)

**文件位置**: `C:\Users\KC\Desktop\POC\Chat-BI-main\frontend\.env`

```env
# ChatBI Frontend Environment Variables
# ===========================================

# ChatBI后端API配置 (智能问答、文件管理、数据集等)
VITE_API_BASE_URL=http://localhost:11434

# Crawler适配后端API配置 (数据爬取管理)
VITE_CRAWLER_API_BASE_URL=http://localhost:8001

# 其他环境变量
# VITE_APP_TITLE=ChatBI
# VITE_APP_VERSION=1.0.0
```

### ChatBI后端配置 (.env)

**文件位置**: `C:\Users\KC\Desktop\POC\Chat-BI-main\backend\.env`

```env
# ===========================================
# ChatBI 环境变量配置文件
# ===========================================

# 🔑 AI模型配置
# SiliconFlow API配置
OPENAI_API_KEY=sk-htjoiirxczzfbhbanimwmwmlmhafzthacgubydjjpmtwbseo

# 14B模型配置
API_URL_14B_CHAT=https://api.siliconflow.cn/v1/chat/completions
API_URL_14B_GENERATE=https://api.siliconflow.cn/v1/chat/completions

# 72B模型配置
API_URL_72B_CHAT=https://api.siliconflow.cn/v1/chat/completions

# Embedding配置
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# 🗄️ 数据库配置
DBHOST=127.0.0.1
DBPORT=5433
DBNAME=chabi_template
DBUSER=aigcgen
DBPGPASSWORD=Louis!123456

# 🔄 缓存和存储
REDIS_URL=redis://localhost:6388/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=chatbi-datasets
MINIO_SECURE=False

# Qdrant向量数据库
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=chatbi_columns

# 🌐 服务配置
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=11434
FASTAPI_ENV=development
FASTAPI_DEBUG=True
FASTAPI_RELOAD=True
FRONTEND_URL=http://localhost:3000
SECRET_KEY=Louis!123456
TOKEN_EXPIRE_MINUTES=30

# 文件上传
MAX_UPLOAD_SIZE=104857600
```

## 🌐 服务访问地址

| 服务 | 地址 | 用途 | 用户名/密码 |
|------|------|------|------------|
| **ChatBI前端** | http://localhost:3000 | 主界面 | - |
| **ChatBI后端API** | http://localhost:11434 | 后端服务 | - |
| **ChatBI API文档** | http://localhost:11434/docs | Swagger文档 | - |
| **Crawler适配API** | http://localhost:8001 | 爬取管理API | - |
| **Crawler API文档** | http://localhost:8001/docs | Swagger文档 | - |
| **MinIO Console** | http://localhost:9001 | 文件管理 | minioadmin / minioadmin123 |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | 向量数据库管理 | - |
| **PostgreSQL** | localhost:5433 | 数据库 | aigcgen / Louis!123456 |
| **Redis** | localhost:6388 | 缓存 | - |

## 📡 API端点说明

### ChatBI后端API (Port: 11434)

| 功能 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 智能问答 | `/api/conversation/create` | POST | 创建对话 |
| 模型配置 | `/api/ai-model-configs` | GET | 获取模型列表 |
| 文件上传 | `/api/dataset/upload` | POST | 上传数据集 |
| 数据集管理 | `/api/dataset/list` | GET | 获取数据集列表 |

### Crawler适配API (Port: 8001)

| 功能 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 数据源管理 | `/api/scraper/sources` | GET | 获取爬取源列表 |
| 定时任务 | `/api/scraper/schedules` | GET | 获取定时任务列表 |
| 爬取结果 | `/api/scraper/results` | GET | 获取爬取结果 |
| 手动爬取 | `/api/scraper/crawl` | POST | 手动触发爬取 |
| 统计信息 | `/api/scraper/stats` | GET | 获取统计信息 |
| 健康检查 | `/api/scraper/health` | GET | 服务健康检查 |

## 🧪 功能测试

### 1. 测试ChatBI基础功能

1. **访问前端**: http://localhost:3000
2. **智能问答测试**:
   - 在输入框中输入问题
   - 选择模型 (Qwen/QwQ-32B)
   - 发送消息，查看AI回复
3. **文件上传测试**:
   - 点击上传按钮，选择CSV文件
   - 确认文件上传成功

### 2. 测试数据爬取管理功能

1. **访问数据爬取管理页面**: http://localhost:3000/#/scraper
2. **功能测试**:
   - 查看数据源列表 (应该显示2个固定源)
   - 查看定时任务列表 (应该显示2个预定义任务)
   - 查看爬取结果列表 (显示历史爬取数据)
   - 测试手动触发爬取功能

### 3. 测试API端点

```bash
# 测试ChatBI后端
curl http://localhost:11434/api/ai-model-configs?user_id=1

# 测试Crawler适配API
curl http://localhost:8001/api/scraper/sources
curl http://localhost:8001/api/scraper/stats
curl http://localhost:8001/api/scraper/health
```

## 🔍 服务状态检查

### 检查所有服务是否正常运行

```bash
# 检查Docker服务
docker-compose ps

# 检查端口占用
netstat -an | findstr ":3000"  # 前端
netstat -an | findstr ":11434" # ChatBI后端
netstat -an | findstr ":8001"  # Crawler后端
netstat -an | findstr ":5433"  # PostgreSQL
netstat -an | findstr ":6388"  # Redis
netstat -an | findstr ":9000"  # MinIO
netstat -an | findstr ":6333"  # Qdrant
```

### 检查服务健康状态

```bash
# ChatBI后端健康检查
curl http://localhost:11434/docs

# Crawler后端健康检查
curl http://localhost:8001/api/scraper/health

# 前端访问检查
curl http://localhost:3000
```

## 🚀 快速启动脚本

### 一键启动脚本 (推荐)

根目录已提供 `启动所有服务.bat` 脚本，可一键启动所有服务：

```batch
# 双击运行或命令行执行
.\启动所有服务.bat
```

### 手动启动脚本

如果需要手动控制启动顺序，可以参考以下脚本：

**启动ChatBI后端和基础设施**:
```batch
@echo off
cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\backend
docker-compose up -d
start "ChatBI Backend" cmd /k "conda activate chatbi && set PYTHONPATH=C:\Users\KC\Desktop\POC\Chat-BI-main\backend && python main.py"
```

**启动Crawler服务**:
```batch
@echo off
cd /d C:\Users\KC\Desktop\POC\crawler+AI-summarizer
start "Crawler Backend" cmd /k "python adapter_api.py"
```

**启动前端服务**:
```batch
@echo off
cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\frontend
start "ChatBI Frontend" cmd /k "pnpm dev"
```

## 🐛 常见问题排查

### 问题1: 前端无法访问后端API

**症状**: 前端显示"无法创建对话"或API调用失败

**排查步骤**:
1. 检查前端.env文件中的`VITE_API_BASE_URL`
2. 确认ChatBI后端服务正常运行
3. 检查CORS配置

**解决方案**:
```bash
# 检查前端配置
cat C:\Users\KC\Desktop\POC\Chat-BI-main\frontend\.env

# 重启ChatBI后端
cd C:\Users\KC\Desktop\POC\Chat-BI-main\backend
python main.py
```

### 问题2: 数据爬取管理页面显示"无可用模型"

**症状**: 爬取管理页面无法加载数据

**排查步骤**:
1. 检查Crawler后端服务是否启动
2. 检查数据库连接
3. 查看后端日志

**解决方案**:
```bash
# 重启Crawler服务
cd C:\Users\KC\Desktop\POC\crawler+AI-summarizer
python adapter_api.py

# 检查数据库连接
python -c "from database import get_db; print('数据库连接正常')"
```

### 问题3: Docker服务启动失败

**症状**: `docker-compose up -d` 失败

**排查步骤**:
1. 检查Docker Desktop是否运行
2. 检查端口占用
3. 检查网络连接

**解决方案**:
```bash
# 重启Docker Desktop
# 检查端口占用
netstat -an | findstr ":5433"
netstat -an | findstr ":6388"
netstat -an | findstr ":9000"
netstat -an | findstr ":6333"

# 清理并重启
docker-compose down
docker-compose up -d
```

### 问题4: 数据库连接失败

**症状**: 后端服务启动失败，显示数据库连接错误

**排查步骤**:
1. 检查PostgreSQL容器是否运行
2. 检查数据库配置
3. 检查端口是否被占用

**解决方案**:
```bash
# 检查Docker服务
docker-compose ps

# 重启数据库服务
docker-compose restart chatbi-postgres

# 检查数据库日志
docker-compose logs chatbi-postgres
```

## 📝 注意事项

1. **端口占用**: 确保以下端口未被占用
   - 3000 (前端)
   - 11434 (ChatBI后端)
   - 8001 (Crawler后端)
   - 5433 (PostgreSQL)
   - 6388 (Redis)
   - 9000 (MinIO)
   - 6333 (Qdrant)

2. **环境依赖**: 确保已安装
   - Docker Desktop
   - Node.js + pnpm
   - Python + conda
   - 所有Python依赖包

3. **数据持久化**: Docker数据卷会自动保存数据，重启服务不会丢失数据

4. **网络配置**: 确保防火墙允许相关端口访问

5. **启动顺序**: 严格按照文档中的启动顺序进行，避免服务依赖问题

## 🎯 功能验证清单

### ✅ ChatBI基础功能
- [ ] 前端页面正常加载 (http://localhost:3000)
- [ ] 模型选择下拉菜单显示可用模型
- [ ] 智能问答功能正常
- [ ] 文件上传功能正常
- [ ] 数据集管理功能正常

### ✅ 数据爬取管理功能
- [ ] 数据源列表显示2个固定源
- [ ] 定时任务列表显示2个预定义任务
- [ ] 爬取结果列表显示历史数据
- [ ] 手动触发爬取功能正常
- [ ] 统计信息显示正确

### ✅ 系统集成
- [ ] 前端可以正常调用后端API
- [ ] 数据爬取管理页面功能完整
- [ ] 所有服务健康检查通过
- [ ] 数据库连接正常

## 🎉 完成！

按照本指南操作后，您将拥有一个完整的ChatBI系统，包括：

- ✅ **智能问答功能** - 自然语言查询，自动生成图表
- ✅ **数据爬取管理** - 自动爬取政府政策文件
- ✅ **AI智能总结** - 自动生成政策文件摘要
- ✅ **文件上传和数据集管理** - 支持多种格式数据上传
- ✅ **多数据集联合分析** - 智能选择相关数据集进行分析
- ✅ **完整的后端API服务** - RESTful API接口
- ✅ **现代化前端界面** - Vue.js构建的响应式界面

**祝使用愉快！** 🚀

---

## 📚 相关文档

- [ChatBI详细文档](./Chat-BI-main/README.md)
- [ChatBI集成启动指南](./crawler+AI-summarizer/ChatBI集成启动指南.md)
- [爬虫项目文档](./crawler+AI-summarizer/项目文档（有的没的全塞进去了）.md)
- [部署指南](./Chat-BI-main/DEPLOYMENT_GUIDE.md)
- [快速开始](./Chat-BI-main/QUICK_START.md)</contents>

