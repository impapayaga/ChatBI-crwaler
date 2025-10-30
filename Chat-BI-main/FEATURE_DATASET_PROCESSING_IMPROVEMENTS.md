# 数据集处理流程改进功能说明

## 概述

优化了数据集上传和处理流程，增强了用户体验和状态可见性。

---

## 新增功能

### 1. ✅ 数据持久化

**数据库字段**（已迁移）:
- `file_md5` - 文件MD5哈希值，用于去重
- `embedding_status` - Embedding状态 (pending/embedding/completed/failed)
- `embedding_progress` - Embedding进度 (0-100)
- `embedding_error` - Embedding错误信息

**验证**:
```bash
cd backend
python -c "from db.session import engine; from sqlalchemy import inspect; import asyncio
async def check():
    async with engine.connect() as conn:
        cols = await conn.run_sync(lambda c: inspect(c).get_columns('sys_dataset'))
        print([c['name'] for c in cols])
asyncio.run(check())"
```

---

### 2. 🎯 后台处理支持

**上传对话框改进**:
- 文件解析完成后，显示"后台处理"按钮
- 用户可以关闭对话框，让embedding在后台继续生成
- 提示用户可以在"我的数据集"中查看进度

**实现位置**: `frontend/src/components/FileUploadDialog.vue:146-154`

**交互流程**:
```
上传文件 → 解析完成 →
  ├─ Embedding生成中 → 点击"后台处理" → 对话框关闭，后台继续
  └─ Embedding完成 → 自动关闭（3秒）
```

---

### 3. ⚠️ 智能状态图标

**数据集列表图标逻辑**:

| 解析状态 | Embedding状态 | 图标 | 颜色 | 说明 |
|---------|--------------|------|------|------|
| failed | - | `mdi-alert-circle` | 红色 | 解析失败 |
| parsing/pending | - | `mdi-loading` (旋转) | 蓝色 | 解析中 |
| parsed | completed | `mdi-check-circle` | 绿色 | ✅ 全部完成 |
| parsed | failed | `mdi-alert` | **黄色** | ⚠️ Embedding失败 |
| parsed | embedding | `mdi-loading` (旋转) | 蓝色 | 🔄 生成中 |
| parsed | pending | `mdi-alert` | **黄色** | ⚠️ 未开始生成 |

**实现位置**: `frontend/src/components/DatasetList.vue:413-459`

**核心逻辑**:
```typescript
// 综合考虑parse和embedding状态
const getDatasetIcon = (dataset: Dataset) => {
  if (dataset.parse_status === 'parsed') {
    if (dataset.embedding_status === 'completed') return 'mdi-check-circle'
    if (dataset.embedding_status === 'failed') return 'mdi-alert'  // 黄色警告
    if (dataset.embedding_status === 'embedding') return 'mdi-loading'
    return 'mdi-alert'  // pending - 黄色警告
  }
  // ...
}
```

---

### 4. 📊 处理流程可视化

**详情对话框 - Timeline展示**:

```
处理流程
  │
  ├─ 步骤 1 - 文件解析
  │   ├─ 状态: 已完成 ✅
  │   ├─ 进度条: 100%
  │   └─ 错误信息（如果失败）
  │
  └─ 步骤 2 - 向量索引生成
      ├─ 状态: 生成中 🔄 / 已完成 ✅ / 生成失败 ⚠️
      ├─ 进度条（生成中）
      ├─ 错误信息（失败时）
      ├─ 重试按钮（失败/pending时）
      └─ 成功提示: "已支持智能语义检索"
```

**实现位置**: `frontend/src/components/DatasetList.vue:169-274`

**特性**:
- Vuetify Timeline组件，清晰展示两个步骤
- 每个步骤独立的状态指示器（圆点颜色 + 图标）
- 实时进度条显示
- 失败时显示详细错误信息
- pending/failed状态下显示操作按钮

---

### 5. 🔄 手动重试功能

**重试Embedding API**:

**端点**: `POST /api/dataset/{dataset_id}/retry_embedding`

**后端实现**: `backend/api/endpoints/dataset_upload.py:315-426`

**功能**:
- 检查数据集状态（必须是parsed）
- 防止重复生成（completed状态拒绝）
- 从数据库读取列信息
- 后台任务重新生成embedding
- 更新状态和进度

**前端集成**:
- **失败状态**: 显示"重新生成向量"按钮（黄色）
- **pending状态**: 显示"开始生成向量"按钮（蓝色）
- 点击后关闭对话框，显示进度提示
- 自动刷新数据集列表

**实现位置**:
- 前端: `frontend/src/components/DatasetList.vue:236-268, 425-445`
- 后端: `backend/api/endpoints/dataset_upload.py:315-426`

---

## 用户体验流程

### 场景1: 正常上传

```
1. 选择文件 → 上传
2. 显示: "正在解析文件" (蓝色进度)
3. 解析完成: "文件解析成功！" ✅
4. 显示: "正在生成向量索引，这可能需要几分钟..." (蓝色进度)
5. 完成: "向量索引生成完成！数据集已可用于智能查询。" ✅
6. 3秒后自动关闭
```

### 场景2: 后台处理

```
1-3. 同上
4. 显示: "正在生成向量索引..."
   → 用户点击"后台处理"
5. 提示: "向量索引将在后台继续生成，您可以在'我的数据集'中查看进度"
6. 对话框关闭
7. 数据集列表显示: 黄色感叹号 (embedding中)
```

### 场景3: Embedding失败

```
1-3. 同上
4. Embedding生成失败
5. 显示: "向量索引生成失败: [错误信息]"
   "注: 数据集仍可用于基本查询"
6. 5秒后关闭
7. 数据集列表显示: 黄色感叹号 ⚠️
8. 查看详情 → 处理流程 → 步骤2显示:
   - 红色错误信息
   - "重新生成向量"按钮
```

### 场景4: 手动重试

```
1. 点击数据集 → 查看详情
2. 看到步骤2: "生成失败" ⚠️
3. 点击"重新生成向量"按钮
4. 提示: "已开始重新生成向量索引，这可能需要几分钟..."
5. 对话框关闭，数据集图标变为蓝色旋转（生成中）
6. 刷新列表查看进度
7. 完成后图标变为绿色 ✅
```

---

## 技术实现细节

### 后端改进

1. **数据库迁移**:
   ```bash
   python migrate_add_embedding_fields.py
   ```

2. **状态管理**:
   ```python
   # dataset_parser.py
   dataset.embedding_status = 'embedding'
   await generate_column_embeddings(...)
   dataset.embedding_status = 'completed'
   # 失败时
   dataset.embedding_status = 'failed'
   dataset.embedding_error = str(e)
   ```

3. **重试API**:
   - 读取 `sys_dataset_column` 表获取列信息
   - 重新调用 `generate_column_embeddings`
   - 后台任务异步执行

### 前端改进

1. **状态追踪**:
   ```typescript
   const parseStatus = ref<'parsing' | 'parsed' | 'failed' | null>(null)
   const embeddingStatus = ref<'pending' | 'embedding' | 'completed' | 'failed' | null>(null)
   ```

2. **智能轮询**:
   ```typescript
   // 检查解析和embedding状态
   if (status === 'parsed') {
     if (embeddingStatus === 'completed') {
       // 全部完成
     } else if (embeddingStatus === 'embedding') {
       // 继续轮询
       setTimeout(checkStatus, 2000)
     }
   }
   ```

3. **图标逻辑**:
   - 综合 `parse_status` 和 `embedding_status`
   - 优先级: failed > embedding/parsing > completed > pending

---

## 测试步骤

### 1. 测试正常流程

```bash
# 1. 启动服务
cd backend && python main.py
cd frontend && pnpm dev

# 2. 上传文件
- 访问 http://localhost:3000
- 点击数据集图标 → 上传文件
- 观察两个阶段的进度

# 3. 验证
- 数据集列表应显示绿色 ✅
- 查看详情，两个步骤都是"已完成"
```

### 2. 测试后台处理

```bash
# 1. 上传文件
# 2. 文件解析完成后，点击"后台处理"
# 3. 验证:
#    - 对话框关闭
#    - 数据集列表显示黄色 ⚠️ 或蓝色 🔄（取决于状态）
# 4. 刷新列表，观察状态变化
# 5. 完成后变为绿色 ✅
```

### 3. 测试重试功能

```bash
# 模拟embedding失败
# 1. 临时停止Qdrant: docker stop qdrant
# 2. 上传文件
# 3. 解析成功，embedding失败
# 4. 查看详情 → 应显示错误信息和"重新生成"按钮
# 5. 启动Qdrant: docker start qdrant
# 6. 点击"重新生成向量"
# 7. 等待完成，验证成功
```

### 4. 测试重复文件

```bash
# 1. 上传文件A
# 2. 再次上传相同文件A
# 3. 应提示: "该文件已上传过，文件名: xxx"
```

---

## API文档

### GET /api/dataset/{dataset_id}/status

**响应**:
```json
{
  "dataset_id": "uuid",
  "name": "文件名.xlsx",
  "parse_status": "parsed",
  "parse_progress": 100,
  "embedding_status": "completed",  // 新增
  "embedding_progress": 100,         // 新增
  "embedding_error": null,            // 新增
  "row_count": 1000,
  "column_count": 20,
  "created_at": "2025-10-19T22:00:00"
}
```

### POST /api/dataset/{dataset_id}/retry_embedding

**请求**: 无body

**响应**:
```json
{
  "success": true,
  "message": "已开始重新生成embedding",
  "dataset_id": "uuid"
}
```

**错误响应**:
```json
{
  "detail": "数据集解析状态为 parsing，无法生成embedding"
}
```

---

## 文件清单

### 后端修改
- ✅ `backend/models/sys_dataset.py` - 添加embedding字段
- ✅ `backend/services/dataset_parser.py` - 独立embedding状态管理
- ✅ `backend/api/endpoints/dataset_upload.py` - 状态返回 + 重试API
- ✅ `backend/migrate_add_embedding_fields.py` - 数据库迁移脚本

### 前端修改
- ✅ `frontend/src/components/FileUploadDialog.vue` - 后台处理按钮
- ✅ `frontend/src/components/DatasetList.vue` - 智能图标 + Timeline + 重试按钮

### 文档
- ✅ `FEATURE_DATASET_PROCESSING_IMPROVEMENTS.md` - 本文档

---

## 已知问题

无

---

## 未来优化

1. **实时进度更新**: WebSocket推送embedding进度（当前是轮询）
2. **批量重试**: 一键重试所有失败的数据集
3. **进度估算**: 根据列数估算embedding时间
4. **通知中心**: 后台任务完成后桌面通知
5. **详细日志**: 在详情中显示处理日志

---

## 更新日期

2025-10-19
