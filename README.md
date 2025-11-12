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
- ✅ Docker Desktop (用于运行基础设施服务) - **必须先启动Docker Desktop！**
- ✅ Node.js + pnpm (前端开发)
- ✅ Python + conda (后端开发)
- ✅ 所有Python依赖包

**⚠️ 重要提示**: 
- 在运行 `docker-compose` 之前，**必须确保 Docker Desktop 正在运行**
- 检查方法：查看系统托盘（右下角）是否有 Docker 图标，或运行 `docker ps` 测试

### 步骤1: 启动Docker基础设施服务

**前置条件**: Docker Desktop 必须已启动并运行

```bash
# 1. 首先验证Docker是否运行
docker ps

# 如果报错 "The system cannot find the file specified"，说明Docker Desktop未运行
# 解决方法：启动Docker Desktop，等待完全启动后再继续

# 2. 进入ChatBI后端目录
cd C:\Users\KC\Desktop\POC\Chat-BI-main\backend

# 3. 启动Docker服务 (PostgreSQL, Redis, MinIO, Qdrant)
docker-compose up -d

# 4. 检查服务状态 - 应该看到4个服务全部运行
docker-compose ps
```

**预期输出**:
- chatbi-postgres (PostgreSQL数据库)
- chatbi-redis (Redis缓存)
- chatbi-minio (MinIO对象存储)
- chatbi-qdrant (Qdrant向量数据库)

**如果Docker启动失败**:
- 确保Docker Desktop已完全启动（系统托盘图标不再显示"正在启动"）
- 尝试重启Docker Desktop
- 检查Windows功能中是否启用了虚拟化（Hyper-V、WSL2等）

### 步骤2: 初始化数据库

**⚠️ 重要**: 必须设置 `PYTHONPATH` 环境变量，否则会报错 `ModuleNotFoundError: No module named 'models'`

```bash
# 进入ChatBI后端目录
cd C:\Users\KC\Desktop\POC\Chat-BI-main\backend

# 激活conda环境
conda activate chatbi

# ⚠️ 关键步骤：设置Python路径（必须！）
# PowerShell:
$env:PYTHONPATH = "C:\Users\KC\Desktop\POC\Chat-BI-main\backend"

# CMD:
set PYTHONPATH=C:\Users\KC\Desktop\POC\Chat-BI-main\backend

# 初始化数据库
python db/init_db.py
```

**如果报错 `ModuleNotFoundError: No module named 'models'`**:
- 说明 `PYTHONPATH` 未设置
- 请按照上面的步骤设置 `PYTHONPATH` 后再运行

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

### 步骤5: 配置前端环境变量（重要！）

**⚠️ 必须步骤**: 前端需要 `.env` 文件才能正确连接后端API

```bash
# 进入ChatBI前端目录
cd C:\Users\KC\Desktop\POC\Chat-BI-main\frontend

# 检查是否存在 .env 文件
# 如果不存在，创建它：

# PowerShell:
@"
VITE_API_BASE_URL=http://localhost:11434
VITE_CRAWLER_API_BASE_URL=http://localhost:8001
"@ | Out-File -FilePath .env -Encoding utf8

# CMD (使用文本编辑器创建):
# 创建 .env 文件，内容如下：
# VITE_API_BASE_URL=http://localhost:11434
# VITE_CRAWLER_API_BASE_URL=http://localhost:8001
```

**如果前端报错 404 或无法连接后端**:
- 检查 `frontend/.env` 文件是否存在
- 确认 `VITE_API_BASE_URL` 的值是否正确
- **重要**: 修改 `.env` 文件后，必须重启前端服务才能生效

### 步骤6: 启动ChatBI前端服务

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

**⚠️ 重要**: 此文件必须存在，否则前端无法连接后端API，会报404错误！

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

**创建方法**:
1. 在 `frontend` 目录下创建 `.env` 文件
2. 复制上面的内容到文件中
3. 保存后重启前端服务（Vite需要重启才能加载环境变量）

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

**⚠️ 重要环境变量说明**:

- `OPENAI_API_KEY`: **必须设置**，用于AI模型调用（SiliconFlow/OpenAI等）
  - 如果未设置，embedding功能将无法使用
  - 即使通过前端配置了模型，系统也会回退到环境变量配置

- `EMBEDDING_MODEL`: Embedding模型名称（默认: text-embedding-3-small）
- `EMBEDDING_DIMENSION`: Embedding向量维度（默认: 4096）

## 🤖 AI模型配置（重要！）

### 首次使用必须配置AI模型

系统启动后，**必须配置AI模型才能正常使用**。模型配置存储在数据库中，需要通过前端界面或API进行配置。

### 配置步骤

#### 1. 访问模型配置页面

1. 打开前端: http://localhost:3000
2. 进入 **"AI模型配置"** 页面（通常在设置或系统配置中）

#### 2. 配置对话模型（Chat Model）

用于智能问答功能，**必须至少配置一个**：

```
配置名称: Qwen 72B Chat
模型类型: 对话模型 (Chat)  ← 重要！
选择提供商: 硅基流动 (SiliconFlow)
API 地址: https://api.siliconflow.cn/v1/chat/completions
API Key: sk-xxxxxxxxxxxxxx (您的API密钥)
模型名称: Qwen/Qwen2.5-72B-Instruct
温度参数: 0.7
最大Token数: 2000
是否默认: ✅ 勾选（重要！）
是否启用: ✅ 勾选
```

#### 3. 配置Embedding模型（必须！）

**⚠️ 关键**: Embedding模型用于数据集向量化，**必须配置且必须设置为默认**，否则向量化功能会失败！

```
配置名称: BGE 中文 1024 维
模型类型: 嵌入模型 (Embedding)  ← 必须是embedding类型！
选择提供商: 硅基流动 (SiliconFlow)
API 地址: https://api.siliconflow.cn/v1/embeddings
API Key: sk-xxxxxxxxxxxxxx (您的API密钥)
模型名称: BAAI/bge-large-zh-v1.5
是否默认: ✅ 必须勾选！（系统只使用默认的embedding配置）
是否启用: ✅ 必须勾选！
配置描述: 中文文本向量化模型，1024维度
```

**配置要求**:
- ✅ `model_type` 必须是 `'embedding'`
- ✅ `is_default` 必须为 `True`（系统只查找默认配置）
- ✅ `is_active` 必须为 `True`（必须启用）

#### 4. 测试连接

配置完成后，**必须点击"测试连接"**确保配置正确：
- 测试通过：显示"连接测试成功"
- 测试失败：检查API地址、API Key是否正确

#### 5. 保存配置

测试通过后，点击"保存配置"。

### 常见问题

**问题1**: 前端测试通过，但向量化报错"未找到有效的embedding配置"
- **原因**: 配置的模型类型不是 `embedding`，而是 `chat`
- **解决**: 创建新的embedding类型配置，或修改现有配置的模型类型

**问题2**: 配置存在但系统找不到
- **原因**: `is_default=False` 或 `is_active=False`
- **解决**: 编辑配置，确保勾选"是否默认"和"是否启用"

**问题3**: 修改配置后仍不生效
- **原因**: 系统有5分钟配置缓存
- **解决**: 等待5分钟或重启后端服务

### 推荐的模型配置

| 模型类型 | 提供商 | 模型名称 | 用途 |
|---------|--------|---------|------|
| Chat | SiliconFlow | Qwen/Qwen2.5-72B-Instruct | 智能问答 |
| Embedding | SiliconFlow | BAAI/bge-large-zh-v1.5 | 中文向量化（推荐） |
| Embedding | OpenAI | text-embedding-3-small | 英文/多语言向量化 |

### 通过API配置（可选）

如果前端无法访问，可以通过API配置：

```bash
# 配置Embedding模型
curl -X POST http://localhost:11434/api/ai-model-configs \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 1,
    "configName": "BGE 中文 1024 维",
    "provider": "siliconflow",
    "modelName": "BAAI/bge-large-zh-v1.5",
    "modelType": "embedding",
    "apiUrl": "https://api.siliconflow.cn/v1/embeddings",
    "apiKey": "sk-您的API密钥",
    "isDefault": true,
    "isActive": true,
    "description": "中文文本向量化模型"
  }'
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

**症状**: `docker-compose up -d` 失败，报错 `unable to get image` 或 `The system cannot find the file specified`

**原因**: Docker Desktop未运行或未完全启动

**排查步骤**:
1. **检查Docker Desktop是否运行**:
   - 查看系统托盘（右下角）是否有Docker图标
   - 运行 `docker ps` 测试连接
   - 如果报错，说明Docker Desktop未运行

2. 检查端口占用
3. 检查网络连接

**解决方案**:
```bash
# 1. 启动Docker Desktop
# 在开始菜单搜索"Docker Desktop"并启动
# 等待完全启动（系统托盘图标不再显示"正在启动"）

# 2. 验证Docker连接
docker ps

# 3. 如果Docker Desktop已运行但仍报错，尝试重启
# 右键系统托盘Docker图标 -> Quit Docker Desktop
# 等待10秒后重新启动

# 4. 检查端口占用
netstat -an | findstr ":5433"
netstat -an | findstr ":6388"
netstat -an | findstr ":9000"
netstat -an | findstr ":6333"

# 5. 清理并重启
docker-compose down
docker-compose up -d
```

**如果Docker Desktop无法启动**:
- 以管理员身份运行Docker Desktop
- 检查Windows功能中是否启用了虚拟化（Hyper-V、WSL2）
- 检查系统资源（内存、磁盘空间）

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

### 问题5: 初始化数据库报错 `ModuleNotFoundError: No module named 'models'`

**症状**: 运行 `python db/init_db.py` 时报错找不到models模块

**原因**: 未设置 `PYTHONPATH` 环境变量

**解决方案**:
```bash
# PowerShell:
$env:PYTHONPATH = "C:\Users\KC\Desktop\POC\Chat-BI-main\backend"
python db/init_db.py

# CMD:
set PYTHONPATH=C:\Users\KC\Desktop\POC\Chat-BI-main\backend
python db/init_db.py
```

### 问题6: 前端报错404，无法连接后端API

**症状**: 前端页面显示"无法创建对话"或API调用返回404

**原因**: 前端缺少 `.env` 文件或环境变量配置错误

**解决方案**:
```bash
# 1. 检查前端.env文件是否存在
cd C:\Users\KC\Desktop\POC\Chat-BI-main\frontend
dir .env

# 2. 如果不存在，创建.env文件
# PowerShell:
@"
VITE_API_BASE_URL=http://localhost:11434
VITE_CRAWLER_API_BASE_URL=http://localhost:8001
"@ | Out-File -FilePath .env -Encoding utf8

# 3. 重启前端服务（重要！修改.env后必须重启）
# 停止当前服务（Ctrl+C），然后重新运行
pnpm dev
```

### 问题7: 向量化失败，报错"未找到有效的embedding配置"

**症状**: 数据集向量化时失败，日志显示"未找到有效的embedding配置"

**原因**: 
1. 未配置embedding模型
2. 配置的模型类型不是 `embedding`
3. 配置未设置为默认（`is_default=False`）
4. 配置未启用（`is_active=False`）

**解决方案**:
1. 访问前端模型配置页面: http://localhost:3000/#/ai-model-config
2. 检查是否有embedding类型的配置
3. 如果没有，创建新的embedding配置：
   - 模型类型: **嵌入模型 (Embedding)** ← 必须是这个！
   - 是否默认: **必须勾选** ← 关键！
   - 是否启用: **必须勾选**
4. 测试连接确保配置正确
5. 保存配置
6. 如果修改后仍不生效，等待5分钟（缓存过期）或重启后端服务

**验证配置**:
```bash
# 通过API检查embedding配置
curl http://localhost:11434/api/embedding-config

# 应该返回配置信息，而不是空值
```

## 📝 注意事项

### 关键配置要求

1. **Docker Desktop必须运行**: 
   - 在运行 `docker-compose` 之前，必须确保Docker Desktop已启动
   - 检查方法: 运行 `docker ps` 测试

2. **PYTHONPATH环境变量**: 
   - 运行 `python db/init_db.py` 时必须设置
   - 运行 `python main.py` 时也必须设置
   - 否则会报错 `ModuleNotFoundError`

3. **前端.env文件**: 
   - 必须创建 `frontend/.env` 文件
   - 否则前端无法连接后端，会报404错误
   - 修改后必须重启前端服务

4. **AI模型配置**: 
   - **必须配置至少一个Chat模型**用于智能问答
   - **必须配置一个Embedding模型**用于向量化，且必须设置为默认
   - Embedding配置要求: `model_type='embedding'`, `is_default=True`, `is_active=True`

5. **端口占用**: 确保以下端口未被占用
   - 3000 (前端)
   - 11434 (ChatBI后端)
   - 8001 (Crawler后端)
   - 5433 (PostgreSQL)
   - 6388 (Redis)
   - 9000 (MinIO)
   - 6333 (Qdrant)

6. **环境依赖**: 确保已安装
   - Docker Desktop（必须先启动）
   - Node.js + pnpm
   - Python + conda
   - 所有Python依赖包

7. **数据持久化**: Docker数据卷会自动保存数据，重启服务不会丢失数据

8. **网络配置**: 确保防火墙允许相关端口访问

9. **启动顺序**: 严格按照文档中的启动顺序进行，避免服务依赖问题

10. **配置缓存**: 
    - 模型配置有5分钟缓存
    - 修改配置后可能需要等待或重启服务才能生效

## 🎯 功能验证清单

### ✅ ChatBI基础功能
- [ ] 前端页面正常加载 (http://localhost:3000)
- [ ] 前端.env文件已创建并配置正确
- [ ] 已配置至少一个Chat模型（用于智能问答）
- [ ] 已配置一个Embedding模型（用于向量化，且设置为默认）
- [ ] 模型选择下拉菜单显示可用模型
- [ ] 智能问答功能正常
- [ ] 文件上传功能正常
- [ ] 数据集管理功能正常
- [ ] 数据集向量化功能正常（验证embedding配置）

### ✅ 数据爬取管理功能
- [ ] 数据源列表显示2个固定源
- [ ] 定时任务列表显示2个预定义任务
- [ ] 爬取结果列表显示历史数据
- [ ] 手动触发爬取功能正常
- [ ] 统计信息显示正确

### ✅ 系统集成
- [ ] Docker Desktop已启动并运行
- [ ] 所有Docker服务正常运行（PostgreSQL, Redis, MinIO, Qdrant）
- [ ] 数据库已初始化（运行了init_db.py）
- [ ] PYTHONPATH环境变量已设置
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

