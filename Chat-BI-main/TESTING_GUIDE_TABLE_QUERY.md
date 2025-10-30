# 表格查询功能测试指南

## 前置准备

### 1. 重建Qdrant Collection (如需要)

如果Qdrant collection的维度配置错误，需要重建：

```python
# backend/reset_qdrant.py
from qdrant_client import QdrantClient
from core.config import settings

client = QdrantClient(url=settings.QDRANT_URL)

# 删除旧collection
try:
    client.delete_collection("chatbi_columns")
    print("旧collection已删除")
except:
    print("collection不存在或已删除")

# 新collection会在上传数据集时自动创建（使用新的4096维度）
print("请重新上传数据集以生成新的embeddings")
```

### 2. 启动服务

```bash
# 后端
cd backend
python main.py

# 前端
cd frontend
pnpm dev
```

### 3. 准备测试数据集

上传一个CSV或Excel文件，例如：
- 销售数据（包含日期、产品、数量、金额等列）
- 用户数据（包含姓名、年龄、地区等列）
- 任何包含数值和类别列的表格数据

## 测试场景

### 场景1: 基础统计查询

**测试步骤:**
1. 上传数据集文件
2. 在前端选择该数据集（数据集卡片）
3. 输入问题："这里面有多少行数据？"

**预期结果:**
- ✅ 前端显示进度指示器
  - 意图识别 → 完成
  - 数据检索 → 完成
  - SQL生成 → 完成
  - 查询执行 → 完成
  - 结果分析 → 完成
- ✅ 后端日志显示SQL: `SELECT COUNT(*) as row_count FROM dataset`
- ✅ 返回行数统计结果
- ✅ 显示数字卡片或简单图表

**后端日志检查点:**
```
✓ 意图分类: query (confidence: 0.95)
✓ 检索到 N 个相关列
✓ LLM生成的SQL: SELECT COUNT(*) as row_count FROM dataset
✓ 查询成功,返回 1 行数据
```

### 场景2: 内容预览查询

**测试步骤:**
1. 继续使用已选择的数据集
2. 输入问题："主要是什么内容？"或"显示数据样例"

**预期结果:**
- ✅ 进度指示器正常显示
- ✅ 后端生成SQL: `SELECT * FROM dataset LIMIT 10` 或选择关键列
- ✅ 返回前10行数据
- ✅ 显示表格或适当的可视化图表

**后端日志检查点:**
```
✓ LLM生成的SQL: SELECT "列1", "列2", ... FROM dataset LIMIT 10
✓ 查询成功,返回 10 行数据
✓ 列名正确使用双引号包裹
```

### 场景3: 聚合统计查询

**测试步骤:**
1. 输入问题："统计各类别的数量" 或 "按地区汇总销售额"

**预期结果:**
- ✅ 进度指示器正常显示
- ✅ 后端生成GROUP BY SQL
- ✅ 返回聚合结果
- ✅ 显示柱状图或饼图

**预期SQL示例:**
```sql
SELECT "类别列", SUM("数值列") as total
FROM dataset
GROUP BY "类别列"
ORDER BY total DESC
LIMIT 100
```

**后端日志检查点:**
```
✓ 检测到聚合意图
✓ 识别出数值列: [...], 分类列: [...]
✓ 生成GROUP BY查询
✓ 查询成功,返回 N 行数据
```

### 场景4: 错误处理测试

#### 4.1 SQL生成失败

**测试步骤:**
1. 输入非常模糊或无关的问题："今天天气怎么样？"

**预期结果:**
- ✅ 意图识别为闲聊(chitchat)
- ✅ 返回友好的文本响应，不执行SQL查询
- ✅ 或者提示用户提供更明确的数据问题

#### 4.2 查询执行失败

**模拟方法:**
手动修改生成的SQL使其包含错误（用于测试事务回滚）

**预期结果:**
- ✅ 进度指示器在"查询执行"步骤显示错误状态
- ✅ 后端日志显示事务回滚
- ✅ 错误消息成功保存到数据库
- ✅ 前端显示友好的错误提示

**后端日志检查点:**
```
✓ SQL查询错误 (第1次尝试): ...
✓ 事务已回滚，清除错误状态
✓ 重新生成SQL查询语句并重试...
```

### 场景5: 多数据集切换

**测试步骤:**
1. 上传多个不同的数据集
2. 先选择数据集A，提问
3. 切换选择数据集B，提问
4. 取消选择所有数据集，提问（普通对话模式）

**预期结果:**
- ✅ 每次正确查询对应的数据集
- ✅ 无数据集时切换到普通对话模式
- ✅ 不会混淆不同数据集的schema

## 前端UI检查清单

### 进度指示器
- [ ] 5个步骤都能正确显示
- [ ] 当前步骤显示旋转动画
- [ ] 完成的步骤显示绿色勾号
- [ ] 错误步骤显示红色警告
- [ ] 错误信息正确显示在相应步骤下

### 数据集选择
- [ ] 数据集卡片显示正常（名称、行数、列数）
- [ ] 选中状态有视觉反馈
- [ ] 可以取消选择
- [ ] 支持多数据集选择（虽然当前只处理第一个）

### 结果展示
- [ ] 图表渲染正常
- [ ] ECharts响应式适配
- [ ] 洞察分析文本格式正确
- [ ] Markdown渲染正常

### 错误处理
- [ ] 错误消息以卡片形式显示（不是alert）
- [ ] 错误信息清晰易懂
- [ ] 提供重试或调整建议

## 后端日志监控

### 关键日志点

1. **向量检索:**
```
✓ Embedding客户端初始化成功: provider=siliconflow, base_url=...
✓ 检索到 N 个相关列, top similarity: 0.XXX
```

2. **SQL生成:**
```
✓ LLM生成的SQL: SELECT ...
✓ 使用回退方案 (如果LLM失败)
```

3. **查询执行:**
```
✓ DuckDB查询成功: N 行
✓ 事务已回滚，清除错误状态 (如果失败)
```

4. **结果处理:**
```
✓ Refined data: {...}
✓ Determined chart type: bar/line/pie
✓ AI回复已保存: conversation_id=...
```

### 错误日志

应该看到的错误（如果发生）：
```
❌ 向量检索失败: ... (dimension mismatch) → 已修复
❌ 生成的SQL包含占位符 → 应使用回退方案
❌ SQL查询错误: relation "table_name" does not exist → 已修复
❌ current transaction is aborted → 应该被回滚处理
```

## 性能基准

### 响应时间目标

- 意图识别: < 2秒
- 向量检索: < 1秒
- SQL生成: < 3秒
- 查询执行: < 2秒（取决于数据量）
- 结果分析: < 5秒（流式返回）

**总体响应时间: 8-15秒**

### 资源使用

监控指标：
- PostgreSQL连接数
- Redis内存使用
- MinIO存储
- Qdrant内存

## 问题排查

### 问题1: 向量检索总是失败

**排查步骤:**
1. 检查Qdrant服务是否运行: `curl http://localhost:6333/collections`
2. 检查collection维度: 应该是4096
3. 检查embedding模型配置
4. 重新上传数据集生成embeddings

**解决方案:**
```bash
# 删除旧collection并重新创建
python backend/reset_qdrant.py
```

### 问题2: SQL总是包含占位符

**排查步骤:**
1. 检查AI模型配置是否正确
2. 检查relevant_columns是否为空
3. 查看SQL生成的prompt是否完整

**解决方案:**
- 确保向量检索正常工作
- 检查回退SQL生成函数是否正常

### 问题3: 事务回滚失败

**排查步骤:**
1. 检查数据库连接池状态
2. 查看PostgreSQL日志
3. 检查session是否正确传递

**解决方案:**
```python
# 确保每次SQL失败后都回滚
await async_session.rollback()
```

### 问题4: 前端进度不更新

**排查步骤:**
1. 检查Vue响应式变量是否正确
2. 检查ProcessingSteps组件是否正确导入
3. 查看浏览器控制台错误

**解决方案:**
- 确保showProcessingSteps.value = true
- 确保currentProcessingStep.value正确更新

## 成功标准

所有测试场景通过，且：

- ✅ 向量检索成功率 > 90%
- ✅ SQL生成成功率 > 95%
- ✅ 查询执行成功率 > 90%
- ✅ 无未处理的事务错误
- ✅ 用户体验流畅，进度可视化
- ✅ 错误处理优雅，信息清晰

## 下一步优化

测试通过后，可以考虑：

1. **性能优化**
   - 添加SQL缓存
   - 优化Qdrant索引
   - 并行处理多个步骤

2. **功能增强**
   - 支持JOIN查询
   - 支持更复杂的筛选条件
   - 支持时间序列分析

3. **用户体验**
   - 实时进度SSE推送
   - 查询历史记录
   - 智能问题推荐

4. **监控告警**
   - 性能监控Dashboard
   - 错误率告警
   - 用户行为分析
