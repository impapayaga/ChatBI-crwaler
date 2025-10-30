# 智能多数据集查询系统升级文档

**升级日期**: 2025-10-20
**版本**: v2.0
**升级类型**: 核心功能增强

---

## 概述

本次升级将 ChatBI 从单数据集查询系统升级为**智能多数据集查询系统**，实现了真正意义上的AI驱动的数据分析能力。

### 升级前的问题

1. **固定表名依赖**：系统依赖预定义的数据库表，当表不存在时查询失败
2. **单数据集限制**：用户选择多个数据集时，前端不会传递给后端
3. **盲目回退机制**：查询失败时会回退到不存在的固定Schema表，导致连续失败
4. **缺乏智能性**：无法根据用户问题自动判断应该使用哪些数据集

### 升级后的能力

✅ **支持1-N个数据集**：用户可以选择任意数量的数据集进行查询
✅ **AI智能选择**：自动分析用户问题，判断需要使用哪些数据集
✅ **动态SQL生成**：根据实际数据集结构动态生成SQL，不依赖固定表名
✅ **多数据集联合查询**：支持跨数据集查询和智能结果合并
✅ **智能错误处理**：用户指定数据集时不再盲目回退到固定Schema

---

## 技术实现

### 1. 前端改进

**文件**: `frontend/src/components/Home.vue`

**修改内容**:
```typescript
// 发送请求时携带用户选中的数据集ID列表
const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/generate_chart`, {
  user_input: userQuestion,
  user_id: 1,
  dataset_ids: selectedDatasets.value.map((d: any) => d.id)  // ✨ 新增
})
```

**影响**: 前端现在会将用户选择的数据集ID列表传递给后端

---

### 2. 后端Schema扩展

**文件**: `backend/api/schemas/user_input.py`

**修改内容**:
```python
from pydantic import BaseModel
from typing import Optional, List

class UserInput(BaseModel):
    user_input: str
    user_id: int = 1
    dataset_ids: Optional[List[str]] = None  # ✨ 新增：支持多数据集
```

**影响**: 后端API现在可以接收数据集ID列表

---

### 3. 智能多数据集查询服务

**新增文件**: `backend/services/multi_dataset_query.py` (400+ 行)

#### 核心功能模块

##### 3.1 获取数据集元数据
```python
async def get_datasets_metadata(
    dataset_ids: List[str],
    async_session: AsyncSession
) -> List[Dict]
```
- 从数据库加载数据集信息
- 获取列名、类型、示例值等元数据
- 支持批量加载多个数据集

##### 3.2 AI智能选择数据集
```python
async def select_relevant_datasets(
    user_query: str,
    datasets_metadata: List[Dict],
    user_id: int = 1
) -> List[str]
```
- 使用LLM分析用户问题
- 判断哪些数据集与问题相关
- 返回需要查询的数据集ID列表

**示例**:
```
用户选择: [销售数据, 客户数据, 产品数据]
用户问题: "销售额最高的客户是谁？"

AI分析: 需要"销售数据"（包含销售额）
返回: [销售数据ID]
```

##### 3.3 动态SQL生成
```python
async def generate_sql_for_multi_datasets(
    user_query: str,
    datasets_metadata: List[Dict],
    user_id: int = 1
) -> Dict[str, str]
```
- 为每个相关数据集生成定制化SQL
- 基于实际列信息，不使用固定表名
- 自动处理时间序列、聚合、分组等查询

**生成示例**:
```sql
-- 数据集1: 生物医药政策数据
SELECT
    EXTRACT(YEAR FROM "发布时间") AS "年份",
    COUNT(*) AS "政策数量"
FROM dataset
WHERE "发布时间" BETWEEN '2020-01-01' AND '2024-12-31'
GROUP BY EXTRACT(YEAR FROM "发布时间")
ORDER BY "年份"
```

##### 3.4 多数据集查询与合并
```python
async def query_multiple_datasets(
    dataset_ids: List[str],
    sql_queries: Dict[str, str]
) -> Optional[pd.DataFrame]
```
- 并发执行多个数据集的查询
- 智能合并结果（concat/join）
- 添加数据来源标记列 `_source_dataset`

##### 3.5 主函数
```python
async def smart_multi_dataset_query(
    user_query: str,
    dataset_ids: List[str],
    async_session: AsyncSession,
    user_id: int = 1
) -> Tuple[Optional[pd.DataFrame], str]
```
- 编排整个查询流程
- 返回查询结果和数据来源描述

---

### 4. 查询逻辑重构

**文件**: `backend/api/endpoints/generate_chart.py`

#### 三层智能决策机制

```python
# 情况1: 用户明确指定数据集（最高优先级）
if user_input.dataset_ids and len(user_input.dataset_ids) > 0:
    logger.info(f"使用前端指定的数据集: {user_input.dataset_ids}")
    data_source = "multi_dataset" if len(user_input.dataset_ids) > 1 else "user_dataset"

    # 使用智能多数据集查询服务
    df, data_source_desc = await smart_multi_dataset_query(
        user_input.user_input,
        user_input.dataset_ids,
        async_session,
        user_id=user_input.user_id
    )

# 情况2: 未指定数据集，使用向量检索自动匹配
else:
    logger.info("前端未指定数据集，使用向量检索自动匹配")
    relevant_columns = await search_relevant_columns(user_input.user_input, top_k=5)

    if relevant_columns and relevant_columns[0]['similarity'] > 0.7:
        # 使用向量检索匹配到的数据集
        dataset_id = relevant_columns[0]['dataset_id']
        # ... 执行查询

# 情况3: 智能错误处理
if df is None or df.empty:
    # 用户指定数据集时，不回退到固定Schema
    if user_input.dataset_ids and len(user_input.dataset_ids) > 0:
        logger.error("用户指定的数据集查询失败，不回退到固定Schema")
        return {
            "error": "用户数据集查询失败",
            "message": "无法从您选择的数据集中查询数据...",
            "is_error": True
        }

    # 只有在未指定数据集时才回退到固定Schema
    logger.info("回退到固定Schema查询")
    # ... 执行固定Schema查询
```

---

### 5. Bug修复

**文件**: `backend/services/duckdb_query.py`

**问题**: DuckDB执行SQL时，Python作用域中的 `dataset` 变量（SQLAlchemy模型对象）与SQL中的表名 `dataset` 冲突

**修复**:
```python
# 修改前
dataset = result.scalar_one_or_none()
parquet_filename = dataset.parsed_path.split('/')[-1]

# 修改后
dataset_info = result.scalar_one_or_none()  # ✨ 重命名变量
parquet_filename = dataset_info.parsed_path.split('/')[-1]
```

**原因**: DuckDB的"replacement scans"特性会自动检测Python作用域中的变量，当发现 `dataset` 时会尝试将其作为数据源，但该变量是SQLAlchemy模型，导致错误。

---

## 功能演示

### 场景1: 单数据集查询

**用户操作**:
1. 选择数据集: "生物医药政策数据"
2. 提问: "2020-2024年政策数量趋势"

**系统处理**:
```
1. 接收dataset_ids: ['c657f527-...']
2. 加载数据集元数据（18列）
3. AI判断: 需要使用"生物医药政策数据"
4. 生成SQL: SELECT EXTRACT(YEAR FROM "发布时间"), COUNT(*) ...
5. 执行查询并返回结果
6. 数据来源: "生物医药政策数据"
```

### 场景2: 多数据集智能选择

**用户操作**:
1. 选择数据集: ["生物医药政策", "科技副总政策", "人才引进政策"]
2. 提问: "生物医药相关的政策有多少？"

**系统处理**:
```
1. 接收3个dataset_ids
2. 加载3个数据集元数据
3. AI分析: "生物医药"关键词 → 只需要"生物医药政策"数据集
4. 仅查询相关数据集
5. 返回精准结果
```

### 场景3: 多数据集联合查询

**用户操作**:
1. 选择数据集: ["2020年政策", "2021年政策", "2022年政策"]
2. 提问: "各年度政策发布趋势对比"

**系统处理**:
```
1. 接收3个dataset_ids
2. AI判断: 需要所有3个数据集
3. 为每个数据集生成SQL
4. 并发执行3个查询
5. 合并结果（添加_source_dataset列标识来源）
6. 返回完整趋势对比图表
```

### 场景4: 无数据集选择（自动匹配）

**用户操作**:
1. 不选择任何数据集
2. 提问: "显示一些数据"

**系统处理**:
```
1. dataset_ids为空
2. 启动向量检索
3. 匹配用户历史上传的数据集
4. 如果相似度>0.7，查询用户数据集
5. 否则，回退到系统预定义表
```

---

## 系统架构变化

### 升级前架构

```
前端选择数据集 → 后端忽略 → 向量检索 → 单一数据集查询
                               ↓ 失败
                         固定Schema查询（失败）
```

### 升级后架构

```
前端选择数据集 → 后端接收dataset_ids
                       ↓
              ┌────────┴────────┐
              ↓                 ↓
        有dataset_ids      无dataset_ids
              ↓                 ↓
      智能多数据集查询      向量检索匹配
              ↓                 ↓
    1. 加载元数据           单数据集查询
    2. AI选择相关集             ↓ 失败
    3. 生成SQL           固定Schema查询
    4. 执行&合并
              ↓ 成功
          返回结果
              ↓ 失败（用户指定）
      返回友好错误（不回退）
```

---

## 性能与可扩展性

### 性能优化

1. **并发查询**: 多数据集查询时并发执行，减少总耗时
2. **元数据缓存**: 数据集列信息从数据库加载后可复用
3. **查询限制**: 自动添加LIMIT保护，防止返回海量数据
4. **临时文件管理**: Parquet文件使用完立即清理

### 可扩展性

1. **动态Schema**: 新数据集上传后自动可用，无需修改代码
2. **插件化SQL生成**: 可轻松添加新的查询模板或规则
3. **多模型支持**: AI模型可配置，支持切换不同的LLM
4. **结果合并策略**: 可扩展concat/join/union等合并方式

---

## 测试建议

### 单元测试

```python
# 测试数据集元数据加载
async def test_get_datasets_metadata():
    dataset_ids = ['uuid1', 'uuid2']
    metadata = await get_datasets_metadata(dataset_ids, session)
    assert len(metadata) == 2
    assert 'columns' in metadata[0]

# 测试AI数据集选择
async def test_select_relevant_datasets():
    query = "销售额趋势"
    datasets = [
        {'id': 'sales', 'logical_name': '销售数据'},
        {'id': 'hr', 'logical_name': '人力资源数据'}
    ]
    selected = await select_relevant_datasets(query, datasets)
    assert 'sales' in selected

# 测试SQL生成
async def test_generate_sql():
    query = "统计行数"
    metadata = [{'id': 'ds1', 'columns': [...]}]
    sqls = await generate_sql_for_multi_datasets(query, metadata)
    assert 'COUNT(*)' in sqls['ds1']
```

### 集成测试

```bash
# 测试1: 单数据集查询
curl -X POST http://localhost:11434/api/generate_chart \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "2020年政策数量",
    "user_id": 1,
    "dataset_ids": ["c657f527-..."]
  }'

# 测试2: 多数据集查询
curl -X POST http://localhost:11434/api/generate_chart \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "各省政策对比",
    "user_id": 1,
    "dataset_ids": ["uuid1", "uuid2", "uuid3"]
  }'

# 测试3: 自动匹配模式
curl -X POST http://localhost:11434/api/generate_chart \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "显示数据",
    "user_id": 1
  }'
```

---

## 回滚方案

如需回滚到升级前版本：

### 1. 前端回滚
```bash
cd frontend
git checkout HEAD~1 src/components/Home.vue
```

### 2. 后端回滚
```bash
cd backend

# 删除新增文件
rm services/multi_dataset_query.py

# 回滚修改的文件
git checkout HEAD~1 api/schemas/user_input.py
git checkout HEAD~1 api/endpoints/generate_chart.py
git checkout HEAD~1 services/duckdb_query.py
```

### 3. 重启服务
```bash
# 重启后端
python main.py

# 重启前端
cd frontend && pnpm dev
```

---

## 已知限制

1. **数据集数量**: 建议单次查询数据集数量 ≤ 5个，避免LLM分析超时
2. **列数限制**: 每个数据集加载前50列元数据，超过部分会被忽略
3. **结果合并**: 当多个数据集列结构完全不同时，合并结果可能包含大量NULL值
4. **LLM依赖**: 数据集选择和SQL生成依赖LLM，如果LLM服务不可用会降级到简单规则

---

## 未来改进方向

### 短期 (1-2周)

- [ ] 添加数据集查询结果缓存
- [ ] 支持更复杂的JOIN查询（跨数据集）
- [ ] 优化LLM提示词，提高SQL生成准确率
- [ ] 添加查询性能监控和日志

### 中期 (1-2个月)

- [ ] 实现数据集关系自动发现（主键/外键）
- [ ] 支持自定义SQL函数
- [ ] 多租户数据隔离
- [ ] 查询历史和收藏功能

### 长期 (3-6个月)

- [ ] 图数据库支持（Neo4j等）
- [ ] 实时流数据查询
- [ ] 自然语言到SQL的持续学习
- [ ] 数据血缘关系可视化

---

## FAQ

### Q1: 为什么有时候选择2个数据集但只查询了1个？

A: 这是AI智能选择的结果。系统会分析你的问题，判断真正需要使用的数据集。例如，你选了"销售数据"和"客户数据"，但问题是"销售额趋势"，系统判断只需要销售数据。

### Q2: 如何强制使用所有选中的数据集？

A: 在问题中明确提及所有数据集，例如："对比销售数据和客户数据"，AI会识别到需要使用两个数据集。

### Q3: 查询报错"数据集未解析完成"怎么办？

A: 检查数据集管理页面，确认数据集的解析状态为"已完成"。如果是"解析中"，请等待；如果是"失败"，需要重新上传。

### Q4: 多数据集合并后列名重复怎么办？

A: 系统会自动添加 `_source_dataset` 列标识数据来源。如果需要区分同名列，可以在问题中明确指定，例如："销售数据中的金额 vs 退款数据中的金额"。

### Q5: 向量检索相似度阈值0.7是否可调整？

A: 是的，在 `backend/api/endpoints/generate_chart.py` 第140行可以修改阈值：
```python
if relevant_columns and relevant_columns[0]['similarity'] > 0.7:  # 修改这里
```

---

## 贡献者

- **核心开发**: Claude Code AI Assistant
- **需求方**: yanluohao
- **测试**: ChatBI开发团队

---

## 变更日志

### v2.0 (2025-10-20)

**新增**:
- 智能多数据集查询服务 (`multi_dataset_query.py`)
- 前端数据集ID传递功能
- AI驱动的数据集选择算法
- 动态SQL生成引擎
- 多数据集结果合并功能

**修复**:
- DuckDB变量名冲突导致的查询失败 (`duckdb_query.py`)
- 盲目回退到不存在的固定Schema表的问题

**改进**:
- 优化错误提示信息
- 增强日志记录
- 提升查询成功率

### v1.0 (2025-10-19)

- 初始版本
- 支持单数据集查询
- 向量检索自动匹配

---

## 许可证

本项目遵循 MIT 许可证

---

**升级完成时间**: 2025-10-20 21:50
**测试状态**: ✅ 已通过基本功能测试
**文档版本**: 1.0
