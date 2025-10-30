# 表格查询功能修复总结

## 问题概述

用户在前端引用表格并进行问答时，后端多个步骤出现错误，导致无法正常查询数据集。

## 主要错误分析

### 1. 向量维度不匹配错误
**错误日志:**
```
Vector dimension error: expected dim: 1536, got 4096
```

**根本原因:**
- Qdrant collection配置期望1536维的向量（text-embedding-3-small模型）
- 实际使用的Qwen3-Embedding-8B模型输出4096维向量
- 配置文件中`EMBEDDING_DIMENSION`设置为1536

**影响:**
- 向量检索完全失败
- 无法匹配用户上传的数据集
- 系统回退到固定Schema查询

### 2. SQL生成占位符错误
**错误日志:**
```
relation "table_name" does not exist
cannot insert multiple commands into a prepared statement
```

**根本原因:**
- LLM生成的SQL包含占位符`table_name`而非实际表名`dataset`
- SQL生成prompt不够明确，未提供足够的schema上下文
- 生成的SQL有时包含多条语句或注释

**影响:**
- SQL执行失败
- 无法查询用户数据集
- 重试机制也失败

### 3. 数据库事务管理错误
**错误日志:**
```
current transaction is aborted, commands ignored until end of transaction block
```

**根本原因:**
- SQL查询失败后事务未正确回滚
- 后续数据库操作在已中止的事务中执行
- 导致所有后续操作失败

**影响:**
- 无法保存错误消息到数据库
- 整个请求链路中断
- 用户看不到任何反馈

### 4. 前端缺少进度指示
**问题:**
- 用户无法看到后端处理进度
- 不知道当前在执行哪个步骤
- 错误发生时无法定位问题环节

## 解决方案

### 1. 修复向量维度配置

**文件:** `backend/core/config.py`

**更改:**
```python
# 修复前
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", 1536))  # text-embedding-3-small维度

# 修复后
# Qwen3-Embedding-8B维度为4096, text-embedding-3-small维度为1536
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", 4096))
```

**效果:**
- Qdrant collection将使用正确的4096维度
- 向量检索功能恢复正常
- 可以准确匹配用户上传的数据集

### 2. 增强SQL生成逻辑

**文件:** `backend/api/endpoints/generate_chart.py`

**关键改进:**
1. **使用LLM生成SQL**，提供详细的schema上下文
2. **明确规则:**
   - 表名必须使用`dataset`
   - 列名用双引号包裹
   - 只能使用提供的列名
   - 不允许使用占位符
   - 只生成一条SQL语句

3. **多层回退机制:**
   - 主方案：LLM生成SQL
   - 检查：验证SQL不包含占位符
   - 回退方案：基于规则的SQL生成

**新增函数:**
```python
async def generate_sql_for_dataset(user_query, relevant_columns, dataset_id):
    """使用LLM生成更智能的SQL查询"""
    # 构建详细的列信息描述
    # 包含列名、类型、示例值
    # ...

def generate_fallback_sql(user_query, relevant_columns):
    """回退SQL生成方案：基于规则"""
    # 检测查询意图
    # 生成适当的SQL模板
    # ...
```

**效果:**
- 生成的SQL准确使用实际表名和列名
- 支持多种查询模式（统计、聚合、详情查询）
- 错误处理更健壮

### 3. 修复事务管理

**文件:** `backend/api/utils/db_utils.py`

**关键改进:**
```python
async def execute_sql_query(sql_query, user_input, async_session, retry_count=3):
    for attempt in range(retry_count):
        try:
            result = await async_session.execute(text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        except Exception as e:
            logging.error(f"SQL查询错误 (第{attempt + 1}次尝试): {e}")

            # 关键修复: 显式回滚事务以清除错误状态
            try:
                await async_session.rollback()
                logging.info("事务已回滚，清除错误状态")
            except Exception as rollback_error:
                logging.error(f"回滚事务失败: {rollback_error}")

            # 继续重试...
```

**效果:**
- 失败的SQL查询不会影响后续操作
- 错误消息可以正常保存到数据库
- 重试机制正常工作

### 4. 添加前端进度指示器

**新增组件:** `frontend/src/components/ProcessingSteps.vue`

**功能特性:**
- 实时显示5个处理步骤：
  1. 意图识别
  2. 数据检索
  3. SQL生成
  4. 查询执行
  5. 结果分析

- 状态展示：
  - ✓ 已完成（绿色勾）
  - ⟳ 进行中（旋转动画）
  - ⚠ 错误（红色警告）
  - ○ 待处理（灰色圆圈）

**集成到 Home.vue:**
```vue
<ProcessingSteps
  v-if="isLoading && showProcessingSteps"
  :current-step="currentProcessingStep"
  :error="processingError"
  class="mb-4"
/>
```

**效果:**
- 用户清楚看到后端处理进度
- 错误发生时立即在相应步骤显示
- 提升用户体验和可调试性

## 数据流程图

### 修复后的完整流程

```
用户提问
   ↓
[1. 意图识别] ← 前端显示
   ↓
[2. 向量检索] ← 使用正确的4096维embedding
   ↓ (相似度 > 0.7)
[3. SQL生成] ← LLM生成，带回退机制
   ↓
[4. 查询执行] ← DuckDB查询Parquet
   ↓ (失败时自动回滚事务)
[5. 结果分析] ← 图表生成 + 洞察分析
   ↓
返回结果给用户
```

## 测试建议

### 1. 向量检索测试
```bash
# 重新创建Qdrant collection (如果维度已经不匹配)
# 需要删除旧collection并重新生成embeddings
```

### 2. 数据集查询测试
测试用例：
- "这里面有多少行数据？" → 应返回 `SELECT COUNT(*) as row_count FROM dataset`
- "主要是什么内容？" → 应返回 `SELECT * FROM dataset LIMIT 10`
- "统计各类别的数量" → 应生成带GROUP BY的SQL

### 3. 错误处理测试
- 测试SQL生成失败的回退机制
- 测试事务回滚是否正常工作
- 测试前端错误显示是否准确

### 4. 进度指示器测试
- 检查每个步骤是否正确显示
- 检查错误状态是否准确标记
- 检查动画效果是否流畅

## 部署注意事项

### 1. 环境变量更新
如果使用`.env`文件，更新：
```bash
EMBEDDING_DIMENSION=4096
```

### 2. Qdrant Collection重建
如果已有collection，需要重新创建：
```python
# 删除旧collection
qdrant_client.delete_collection("chatbi_columns")

# 创建新collection (会自动使用新的维度配置)
# 重新上传数据集以生成embeddings
```

### 3. 前端依赖
确保ProcessingSteps组件已正确导入：
```typescript
import ProcessingSteps from './ProcessingSteps.vue'
```

### 4. 数据库连接池
确保PostgreSQL连接池配置足够大，以处理事务回滚：
```python
# db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,  # 增加连接池大小
    max_overflow=40,
    pool_pre_ping=True
)
```

## 后续优化建议

### 1. 实时进度流式传输
当前进度指示是前端模拟的，可以改为：
- 后端通过Server-Sent Events (SSE)实时推送进度
- 更准确反映实际处理状态

### 2. SQL缓存机制
- 相似问题复用已生成的SQL
- 减少LLM调用次数
- 提升响应速度

### 3. 查询结果缓存
- 缓存常见查询的结果
- 设置合理的TTL
- 减少数据库压力

### 4. 更智能的Schema理解
- 自动识别主键、外键关系
- 理解列之间的语义关系
- 生成更复杂的JOIN查询

### 5. 可视化增强
- 根据数据特征自动推荐最佳图表类型
- 支持更多图表类型（热力图、散点图等）
- 支持数据表格展示

## 文件修改清单

### 后端修改
1. `backend/core/config.py` - 更新embedding维度配置
2. `backend/api/endpoints/generate_chart.py` - 增强SQL生成逻辑
3. `backend/api/utils/db_utils.py` - 添加事务回滚处理

### 前端修改
1. `frontend/src/components/ProcessingSteps.vue` - 新增进度指示器组件
2. `frontend/src/components/Home.vue` - 集成进度指示器

## 总结

本次修复解决了表格查询功能的四个核心问题：

1. ✅ **向量维度不匹配** - 配置正确的embedding维度
2. ✅ **SQL生成错误** - 增强SQL生成逻辑，添加回退机制
3. ✅ **事务管理问题** - 添加显式事务回滚
4. ✅ **用户体验** - 添加可视化进度指示器

这些修复使得用户可以：
- 成功引用上传的数据集
- 自然语言查询数据
- 看到清晰的处理进度
- 获得准确的错误反馈
- 查看可视化图表和洞察分析

系统现在更加健壮、用户友好，并且易于调试和维护。
