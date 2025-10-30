# ChatBI 文件上传与动态问数 - 部署指南

## 📋 功能概述

本次升级为ChatBI添加了以下核心功能:

1. **文件上传** - 支持CSV和Excel文件上传
2. **自动解析** - 自动推断Schema并转换为Parquet格式
3. **向量检索** - 基于pgvector的列级语义检索
4. **意图识别** - 自动区分闲聊/查询/可视化请求
5. **动态问数** - 同时支持固定Schema和用户上传数据集的查询

---

## 🏗️ 架构升级

### 新增组件

| 组件 | 版本 | 用途 |
|-----|------|------|
| **MinIO** | latest | 对象存储(原始文件+Parquet) |
| **pgvector** | latest | PostgreSQL向量扩展 |
| **DuckDB** | 0.9.0+ | 查询Parquet文件 |
| **OpenAI API** | - | 生成embedding + 意图识别 |

### 数据流程

```
用户上传Excel → MinIO存储 → 后台解析 → Parquet转换
                                    ↓
                          生成列级Embedding → pgvector
                                    ↓
用户问数 → 意图识别 → 向量检索相关列 → DuckDB查询 → ECharts渲染
```

---

## 🚀 快速部署(10分钟)

### 步骤1: 安装依赖

```bash
# 进入后端目录
cd backend

# 安装Python依赖(conda环境)
conda activate chatbi
pip install -r requirements.txt
```

**新增依赖包:**
- `minio>=7.2.0` - MinIO客户端
- `pyarrow>=14.0.0` - Parquet读写
- `openpyxl>=3.1.0` - Excel解析
- `duckdb>=0.9.0` - 列式数据库
- `pgvector>=0.2.0` - 向量数据库
- `openai>=1.10.0` - OpenAI API

---

### 步骤2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件,填写必要配置
vim .env
```

**必填配置项:**

```env
# OpenAI API Key (必填!)
OPENAI_API_KEY=sk-your-actual-api-key-here

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Redis配置
REDIS_URL=redis://localhost:6388/0
```

---

### 步骤3: 启动基础设施

```bash
# 启动Docker服务(PostgreSQL + Redis + MinIO)
cd backend
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**服务端口:**
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6388`
- MinIO API: `localhost:9000`
- MinIO Console: `localhost:9001` (浏览器访问)

---

### 步骤4: 初始化数据库

```bash
# 进入backend目录
cd backend

# 运行数据库初始化(会自动创建表+pgvector扩展)
python init_db.py
```

**初始化内容:**
- 创建现有表(`sys_user`, `sys_conversation`等)
- 创建新表(`sys_dataset`, `sys_dataset_column`, `sys_dataset_action`)
- 创建pgvector扩展和`sys_column_embedding`向量表

---

### 步骤5: 启动后端服务

```bash
# 确保conda环境激活
conda activate chatbi

# 启动FastAPI
python main.py
```

**验证:**
- 访问 http://127.0.0.1:11434/docs 查看API文档
- 应该看到新的API端点: `/api/upload_dataset`, `/api/datasets` 等

---

### 步骤6: 启动前端

```bash
# 进入前端目录
cd frontend

# 安装依赖(如果之前未安装)
pnpm install

# 启动开发服务器
pnpm dev
```

**访问:** http://localhost:3000

---

## 🧪 功能测试

### 测试1: 文件上传

使用curl测试上传API:

```bash
curl -X POST http://127.0.0.1:11434/api/upload_dataset \
  -F "file=@test_data.csv" \
  -F "logical_name=销售数据" \
  -F "description=2024年销售记录"
```

**预期响应:**

```json
{
  "dataset_id": "uuid-here",
  "status": "parsing",
  "message": "文件上传成功,正在后台解析...",
  "file_name": "test_data.csv",
  "file_size": 12345
}
```

---

### 测试2: 查询解析状态

```bash
curl http://127.0.0.1:11434/api/dataset/{dataset_id}/status
```

**预期响应:**

```json
{
  "dataset_id": "uuid",
  "name": "test_data.csv",
  "parse_status": "parsed",  // pending/parsing/parsed/failed
  "parse_progress": 100,
  "row_count": 1000,
  "column_count": 10
}
```

---

### 测试3: 向量检索

测试语义检索功能:

```python
# 在backend目录运行Python
from services.embedding_service import search_relevant_columns
import asyncio

async def test():
    results = await search_relevant_columns("销售金额", top_k=5)
    print(results)

asyncio.run(test())
```

**预期输出:**

```python
[
    {
        'dataset_id': 'uuid',
        'col_name': 'sales_amount',
        'similarity': 0.92,
        'dataset_name': '销售数据.csv'
    },
    ...
]
```

---

## 📊 MinIO管理界面

访问 http://localhost:9001

**登录凭据:**
- Username: `minioadmin`
- Password: `minioadmin123`

**查看上传的文件:**
- Bucket: `chatbi-datasets`
- `uploads/` - 原始CSV/Excel文件
- `parquet/` - 转换后的Parquet文件

---

## 🔧 故障排查

### 问题1: MinIO连接失败

**症状:** 上传文件时报错 `MinIO connection refused`

**解决:**

```bash
# 检查MinIO服务状态
docker-compose ps minio

# 重启MinIO
docker-compose restart minio

# 检查端口占用
lsof -i :9000
```

---

### 问题2: pgvector扩展未安装

**症状:** 数据库初始化时报错 `extension "vector" does not exist`

**解决:**

```bash
# 进入PostgreSQL容器
docker exec -it chatbi-poc psql -U aigcgen -d chabi_template

# 手动创建扩展
CREATE EXTENSION IF NOT EXISTS vector;
\dx  # 验证扩展已安装
```

---

### 问题3: Embedding生成失败

**症状:** 日志显示 `OpenAI客户端未初始化`

**解决:**

1. 检查 `.env` 文件中 `OPENAI_API_KEY` 是否配置
2. 验证API Key有效性:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

3. 如果没有OpenAI Key,可以暂时跳过Embedding(仅影响语义检索,不影响上传)

---

### 问题4: 文件解析卡在parsing状态

**症状:** 上传后长时间停留在 `parse_status: parsing`

**解决:**

1. 查看后端日志:

```bash
# 查看FastAPI日志
tail -f backend/logs/app.log
```

2. 检查后台任务错误:

```python
# 手动触发解析
from services.dataset_parser import parse_dataset_task
import asyncio

asyncio.run(parse_dataset_task("dataset_id_here", "file_path", "filename.csv"))
```

---

## 🎯 API端点清单

### 新增API端点

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/api/upload_dataset` | POST | 上传CSV/Excel文件 |
| `/api/dataset/{id}/status` | GET | 查询解析状态 |
| `/api/datasets` | GET | 获取数据集列表 |
| `/api/dataset/{id}` | DELETE | 删除数据集 |

### 现有API端点(保持兼容)

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/api/generate_chart` | POST | 生成图表(已升级) |
| `/api/insight_analysis_stream` | POST | 流式洞察分析 |
| `/api/ai_model_config` | GET/POST | AI模型配置 |

---

## 📈 性能优化建议

### 1. Embedding缓存

对于相同的列名+示例值组合,可以缓存embedding结果:

```python
# 在embedding_service.py中添加Redis缓存
cache_key = f"embedding:{hash(description)}"
cached = await redis_client.get(cache_key)
if cached:
    return json.loads(cached)
```

### 2. Parquet分片

对于大文件(>1GB),建议分片存储:

```python
# 在dataset_parser.py中
pq.write_table(table, parquet_buffer, row_group_size=100000)
```

### 3. DuckDB查询缓存

对于热点查询,使用Redis缓存结果:

```python
cache_key = f"query:{hash(sql)}"
cached_result = await redis_client.get(cache_key)
```

---

## 🔐 安全建议

### 1. 生产环境配置

```env
# 修改默认凭据
MINIO_ACCESS_KEY=production-access-key-change-me
MINIO_SECRET_KEY=production-secret-key-change-me

# 启用HTTPS
MINIO_SECURE=True
```

### 2. 文件类型验证

已在代码中实现MIME类型检查和扩展名验证,建议添加病毒扫描:

```python
# 使用clamav扫描上传文件
import pyclamd
cd = pyclamd.ClamdUnixSocket()
scan_result = cd.scan_stream(file_data)
```

### 3. SQL注入防护

已使用参数化查询,但建议添加SQL校验层:

```python
from sqlparse import format, parse
# 验证生成的SQL语句
```

---

## 📚 下一步开发建议

### 短期(1-2周)

1. **前端文件上传组件** - 在ChatInput中添加文件上传按钮
2. **DuckDB集成** - 实现Parquet文件查询
3. **NL→SQL改造** - 支持用户数据集的动态Schema

### 中期(1个月)

1. **多表关联** - 支持JOIN查询
2. **Celery队列** - 替换BackgroundTasks,支持分布式
3. **数据集管理页面** - 查看、编辑、删除数据集

### 长期(3个月)

1. **数据血缘** - 记录数据转换链路
2. **权限管理** - 数据集级别权限控制
3. **数据质量检测** - 自动检测数据异常

---

## 💡 成本估算

### OpenAI API成本

**Embedding成本:**
- text-embedding-3-small: $0.00002 / 1K tokens
- 平均每列描述: ~50 tokens
- 100列数据集: 约 $0.0001 (几乎可以忽略)

**意图识别成本:**
- gpt-4o-mini: $0.00015 / 1K tokens
- 每次查询: ~100 tokens
- 1000次查询: 约 $0.015

**总结:** 每月1000个数据集 + 10000次查询 ≈ $1.6

---

## 🆘 获取帮助

- **问题反馈:** 在项目根目录创建 `issues.md`
- **查看日志:** `tail -f backend/logs/*.log`
- **数据库调试:** `docker exec -it chatbi-poc psql -U aigcgen -d chabi_template`

---

## ✅ 检查清单

部署前请确认:

- [ ] Docker服务正常运行 (`docker-compose ps`)
- [ ] `.env` 文件已配置OpenAI API Key
- [ ] PostgreSQL包含pgvector扩展 (`\dx` 命令检查)
- [ ] MinIO Console可访问 (http://localhost:9001)
- [ ] Python依赖已安装 (`pip list | grep minio`)
- [ ] 数据库表已创建 (`\dt` 命令检查)

---

**部署完成!** 🎉

现在您的ChatBI系统已支持用户上传CSV/Excel文件并进行智能问数。
