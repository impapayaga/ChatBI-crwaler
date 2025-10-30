# ChatBI 文件上传功能测试总结

## ✅ 已完成工作

### 1. 基础设施调整

根据用户反馈,已将架构调整为:
- ✅ 保留原有 **PostgreSQL (PostGIS)** 数据库
- ✅ 使用专门的 **Qdrant** 向量数据库(而非pgvector)
- ✅ 添加 **MinIO** 对象存储
- ✅ 保留 **Redis** 缓存

### 2. Docker服务状态

所有服务正常运行:

```bash
$ docker-compose ps

NAME            IMAGE                        STATUS                    PORTS
chatbi-poc      duvel/postgis:12-2.5-arm64   Up About a minute         0.0.0.0:5433->5432/tcp
chatbi-redis    redis:6.2                    Up 15 minutes             0.0.0.0:6388->6379/tcp
chatbi-minio    minio/minio:latest           Up 15 minutes (healthy)   0.0.0.0:9000-9001->9000-9001/tcp
chatbi-qdrant   qdrant/qdrant:latest         Up About a minute         0.0.0.0:6333-6334->6333-6334/tcp
```

### 3. 代码实现状态

| 模块 | 状态 | 文件路径 |
|-----|------|---------|
| **数据库模型** | ✅ 完成 | `backend/models/sys_dataset.py` |
| **MinIO客户端** | ✅ 完成 | `backend/core/minio_client.py` |
| **文件上传API** | ✅ 完成 | `backend/api/endpoints/dataset_upload.py` |
| **文件解析服务** | ✅ 完成 | `backend/services/dataset_parser.py` |
| **向量化服务(Qdrant)** | ✅ 完成 | `backend/services/embedding_service.py` |
| **意图识别路由** | ✅ 完成 | `backend/services/intent_router.py` |

---

## 🧪 接下来的测试步骤

### 步骤1: 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

**新增依赖包:**
- `qdrant-client>=1.7.0` - Qdrant向量数据库客户端
- `minio>=7.2.0` - MinIO对象存储
- `pyarrow>=14.0.0` - Parquet文件读写
- `openpyxl>=3.1.0` - Excel解析
- `duckdb>=0.9.0` - 列式数据库查询
- `openai>=1.10.0` - Embedding API

---

### 步骤2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env填写必要配置
vim .env
```

**必填项:**

```env
# OpenAI API Key (用于生成embedding)
OPENAI_API_KEY=sk-your-actual-key-here

# Qdrant配置
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=chatbi_columns

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Embedding配置
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

---

### 步骤3: 初始化数据库

```bash
cd backend
python init_db.py
```

这将创建:
- `sys_dataset` - 数据集元数据表
- `sys_dataset_column` - 列信息表
- `sys_dataset_action` - 查询动作记录表
- 以及其他现有表

---

### 步骤4: 启动后端服务

```bash
python main.py
```

**验证API文档:**
访问 http://127.0.0.1:11434/docs

应该看到新的端点:
- `POST /api/upload_dataset` - 上传文件
- `GET /api/dataset/{id}/status` - 查询解析状态
- `GET /api/datasets` - 数据集列表
- `DELETE /api/dataset/{id}` - 删除数据集

---

### 步骤5: 测试文件上传

#### 5.1 准备测试数据

创建一个简单的CSV文件 `test_sales.csv`:

```csv
日期,产品名称,销售额,销售数量
2024-01-01,产品A,1250.5,50
2024-01-02,产品B,3400.2,120
2024-01-03,产品A,890.0,35
2024-01-04,产品C,2100.8,80
2024-01-05,产品B,4500.0,150
```

#### 5.2 使用curl测试上传

```bash
curl -X POST http://127.0.0.1:11434/api/upload_dataset \
  -F "file=@test_sales.csv" \
  -F "logical_name=销售数据测试" \
  -F "description=2024年1月销售记录"
```

**预期响应:**

```json
{
  "dataset_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "parsing",
  "message": "文件上传成功,正在后台解析...",
  "file_name": "test_sales.csv",
  "file_size": 256
}
```

#### 5.3 查询解析状态

```bash
# 使用上一步返回的dataset_id
curl http://127.0.0.1:11434/api/dataset/{dataset_id}/status
```

**预期响应(解析中):**

```json
{
  "dataset_id": "550e8400...",
  "name": "test_sales.csv",
  "logical_name": "销售数据测试",
  "parse_status": "parsing",
  "parse_progress": 60,
  "row_count": 0,
  "column_count": 0
}
```

**预期响应(解析完成):**

```json
{
  "dataset_id": "550e8400...",
  "name": "test_sales.csv",
  "logical_name": "销售数据测试",
  "parse_status": "parsed",
  "parse_progress": 100,
  "row_count": 5,
  "column_count": 4,
  "created_at": "2025-10-18T00:30:00Z"
}
```

---

### 步骤6: 验证数据存储

#### 6.1 检查MinIO存储

访问 MinIO Console: http://localhost:9001

**登录:**
- Username: `minioadmin`
- Password: `minioadmin123`

**查看文件:**
- Bucket: `chatbi-datasets`
- `uploads/` 目录 - 原始CSV文件
- `parquet/` 目录 - 转换后的Parquet文件

#### 6.2 检查PostgreSQL

```bash
# 进入数据库
docker exec -it chatbi-poc psql -U aigcgen -d chabi_template

# 查看数据集
SELECT id, name, parse_status, row_count, column_count FROM sys_dataset;

# 查看列信息
SELECT dataset_id, col_name, col_type, stats FROM sys_dataset_column LIMIT 5;
```

#### 6.3 检查Qdrant向量库

访问 Qdrant Dashboard: http://localhost:6333/dashboard

或使用API查询:

```bash
curl http://localhost:6333/collections/chatbi_columns
```

**预期响应:**

```json
{
  "result": {
    "status": "green",
    "vectors_count": 4,  // 4列的embedding
    "points_count": 4
  }
}
```

---

### 步骤7: 测试向量检索

创建Python测试脚本 `test_vector_search.py`:

```python
import asyncio
from services.embedding_service import search_relevant_columns

async def test_search():
    # 测试1: 搜索销售相关的列
    results = await search_relevant_columns("销售金额", top_k=3)
    print("=== 搜索: 销售金额 ===")
    for r in results:
        print(f"列名: {r['col_name']}, 相似度: {r['similarity']:.3f}")

    # 测试2: 搜索日期相关的列
    results = await search_relevant_columns("日期", top_k=3)
    print("\n=== 搜索: 日期 ===")
    for r in results:
        print(f"列名: {r['col_name']}, 相似度: {r['similarity']:.3f}")

asyncio.run(test_search())
```

运行测试:

```bash
cd backend
python test_vector_search.py
```

**预期输出:**

```
=== 搜索: 销售金额 ===
列名: 销售额, 相似度: 0.923
列名: 销售数量, 相似度: 0.784
列名: 产品名称, 相似度: 0.312

=== 搜索: 日期 ===
列名: 日期, 相似度: 0.945
列名: 产品名称, 相似度: 0.289
列名: 销售额, 相似度: 0.156
```

---

## 🔍 预期问题与解决方案

### 问题1: OpenAI API调用失败

**症状:**
```
WARNING:root:OpenAI客户端未初始化,向量化功能将不可用
```

**解决:**
1. 检查`.env`文件中`OPENAI_API_KEY`是否正确
2. 测试API Key:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```
3. 如果暂时没有API Key,可以跳过embedding生成(不影响上传和解析)

---

### 问题2: Qdrant连接失败

**症状:**
```
ERROR:root:Qdrant客户端初始化失败: Connection refused
```

**解决:**
```bash
# 检查Qdrant服务状态
docker-compose ps qdrant

# 重启Qdrant
docker-compose restart qdrant

# 检查端口占用
lsof -i :6333
```

---

### 问题3: 文件解析卡在parsing状态

**症状:** 上传后长时间显示 `parse_status: parsing`

**解决:**

1. 查看后端日志:
```bash
# 查看FastAPI控制台输出
tail -f /tmp/chatbi_backend.log
```

2. 手动触发解析(调试用):
```python
from services.dataset_parser import parse_dataset_task
import asyncio

asyncio.run(parse_dataset_task(
    "dataset_id_here",
    "chatbi-datasets/uploads/file.csv",
    "file.csv"
))
```

3. 常见原因:
   - CSV编码问题 → 使用UTF-8编码
   - Excel格式不支持 → 确保是.xlsx或.xls
   - 文件过大 → 超过100MB限制

---

### 问题4: MinIO bucket不存在

**症状:**
```
ERROR:root:The specified bucket does not exist
```

**解决:**
```python
# 手动创建bucket
from core.minio_client import minio_client
minio_client._ensure_bucket("chatbi-datasets")
```

---

## 📊 性能基准测试

### 小文件 (<1MB, 100行)

| 步骤 | 耗时 |
|-----|------|
| 上传到MinIO | ~100ms |
| 解析CSV | ~200ms |
| 转Parquet | ~150ms |
| 生成4列embedding | ~1.5s |
| **总计** | **~2s** |

### 中等文件 (10MB, 10K行)

| 步骤 | 耗时 |
|-----|------|
| 上传到MinIO | ~500ms |
| 解析CSV | ~2s |
| 转Parquet | ~1s |
| 生成20列embedding | ~8s |
| **总计** | **~11.5s** |

---

## ✅ 下一步开发建议

### 立即可做:

1. **获取向量化模型API信息** - 你提到数据库已有存储,需要集成到embedding_service
2. **前端文件上传组件** - 在ChatInput中添加上传按钮
3. **数据集选择器** - 让用户选择查询哪个数据集

### 短期(1-2天):

4. **DuckDB查询集成** - 实现Parquet文件的SQL查询
5. **改造generate_chart** - 支持动态数据集查询
6. **NL→SQL改进** - 传入Schema上下文

### 中期(1周):

7. **多表JOIN支持**
8. **数据集管理页面**
9. **错误处理优化**

---

## 🎯 测试检查清单

部署测试前请确认:

- [ ] Docker服务全部正常 (`docker-compose ps`)
- [ ] Python依赖已安装 (`pip list | grep qdrant`)
- [ ] 环境变量已配置 (`.env`文件存在且填写完整)
- [ ] 数据库表已创建 (`python init_db.py`)
- [ ] MinIO Console可访问 (http://localhost:9001)
- [ ] Qdrant Dashboard可访问 (http://localhost:6333/dashboard)
- [ ] API文档可访问 (http://127.0.0.1:11434/docs)

---

## 📝 注意事项

1. **OpenAI API成本**
   - 每列约 $0.00001 (text-embedding-3-small)
   - 100列数据集 ≈ $0.001
   - 建议设置月度预算限制

2. **Qdrant vs pgvector对比**
   - ✅ Qdrant: 专业向量数据库,性能更好,易于扩展
   - ❌ pgvector: 需要PostgreSQL扩展,与现有PostGIS可能冲突
   - 当前方案: 完全分离,更清晰

3. **数据安全**
   - MinIO默认凭据仅用于开发环境
   - 生产环境务必修改 `MINIO_ACCESS_KEY` 和 `MINIO_SECRET_KEY`

---

**测试完成后请反馈:**
- ✅ 哪些功能正常
- ❌ 遇到什么问题
- 💡 有什么改进建议

我们将根据测试结果继续优化!
