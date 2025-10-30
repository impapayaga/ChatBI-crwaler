# 文件上传功能集成测试指南

## ✅ 已完成的前端集成

### 1. 新增组件

| 组件 | 路径 | 功能 |
|-----|------|-----|
| **FileUploadDialog.vue** | `frontend/src/components/FileUploadDialog.vue` | 文件上传对话框，支持CSV/Excel上传 |
| **DatasetList.vue** | `frontend/src/components/DatasetList.vue` | 数据集列表显示，支持查看、选择、删除 |

### 2. 修改的组件

| 组件 | 修改内容 |
|-----|---------|
| **ChatInput.vue** | 添加 `uploadClick` 事件，点击附件图标触发上传 |
| **Home.vue** | 集成 FileUploadDialog 和 DatasetList，添加数据集管理逻辑 |

### 3. 核心功能

#### 文件上传流程
1. 用户点击输入框的附件图标 (📎)
2. 弹出文件上传对话框
3. 选择 CSV/Excel 文件（最大 100MB）
4. 填写数据集名称和描述
5. 点击"上传"按钮
6. 显示上传进度条
7. 后台解析文件（轮询状态）
8. 解析成功后自动关闭对话框
9. 刷新数据集列表

#### 数据集列表
1. 顶部工具栏显示数据集图标 🗄️ (带徽章显示数量)
2. 点击图标展开数据集列表
3. 列表显示：
   - 数据集名称
   - 解析状态（pending/parsing/parsed/failed）
   - 数据规模（行数 × 列数）
4. 支持操作：
   - 选择数据集（用于查询）
   - 查看详情
   - 删除数据集

---

## 🧪 测试步骤

### 前置条件

1. **确保后端服务运行**
```bash
cd backend
# 启动 Docker 服务
docker-compose up -d

# 检查服务状态
docker-compose ps
# 应该看到：chatbi-postgres, chatbi-redis, chatbi-minio, chatbi-qdrant 全部 Up

# 启动后端
python main.py
```

2. **确保前端服务运行**
```bash
cd frontend
pnpm dev
# 访问 http://localhost:3000
```

---

### 测试用例 1: 上传 CSV 文件

#### 1.1 准备测试数据

创建文件 `test_sales.csv`:
```csv
日期,产品名称,销售额,销售数量
2024-01-01,产品A,1250.5,50
2024-01-02,产品B,3400.2,120
2024-01-03,产品A,890.0,35
2024-01-04,产品C,2100.8,80
2024-01-05,产品B,4500.0,150
```

#### 1.2 执行上传
1. 打开应用 http://localhost:3000
2. 点击输入框左侧的 📎 图标
3. 选择 `test_sales.csv`
4. 数据集名称自动填充为 `test_sales`（可修改为"销售数据测试"）
5. 描述填写："2024年1月销售记录"
6. 点击"上传"

#### 1.3 预期结果
- ✅ 上传进度条从 0% → 100%
- ✅ 显示"正在解析文件，请稍候..."
- ✅ 约 2-5 秒后显示"文件解析成功！"
- ✅ 弹出提示："数据集上传成功！您现在可以使用这个数据集进行查询了。"
- ✅ 对话框自动关闭
- ✅ 数据集图标显示徽章 "1"

#### 1.4 验证后端存储

**检查 MinIO:**
```
访问 http://localhost:9001
登录: minioadmin / minioadmin123
Bucket: chatbi-datasets
  - uploads/xxx.csv (原始文件)
  - parquet/xxx.parquet (转换后的文件)
```

**检查 PostgreSQL:**
```bash
docker exec -it chatbi-postgres psql -U aigcgen -d chabi_template

SELECT id, name, logical_name, parse_status, row_count, column_count
FROM sys_dataset;

# 预期输出:
# id | name | logical_name | parse_status | row_count | column_count
# --- | ---- | ------------ | ------------ | --------- | ------------
# xxx | test_sales.csv | 销售数据测试 | parsed | 5 | 4
```

**检查 Qdrant:**
```bash
curl http://localhost:6333/collections/chatbi_columns

# 预期: vectors_count = 4 (4列的embedding)
```

---

### 测试用例 2: 查看数据集列表

#### 2.1 点击数据集图标
1. 在顶部工具栏找到数据集图标 🗄️（右上角）
2. 点击图标展开列表

#### 2.2 预期结果
- ✅ 显示数据集列表
- ✅ "销售数据测试" 显示绿色 ✓ 图标（已解析）
- ✅ 副标题显示 "5 行 × 4 列"

#### 2.3 查看详情
1. 点击数据集右侧的 "⋮" 菜单
2. 选择"查看详情"

#### 2.4 预期结果
- ✅ 弹出详情对话框
- ✅ 显示文件名、数据规模、解析状态、描述、上传时间

---

### 测试用例 3: 使用数据集查询

#### 3.1 选择数据集
1. 在数据集列表中点击"销售数据测试"
2. 或点击 "⋮" → "选择数据集"

#### 3.2 预期结果
- ✅ 输入框自动填充："分析销售数据测试的数据"

#### 3.3 执行查询
在输入框输入以下问题（任选其一）：
- "销售额最高的产品是什么？"
- "显示每个产品的总销售额"
- "哪天的销售数量最多？"

点击发送 ↑

#### 3.4 预期结果（基于后端实现）

**方案 A: 向量相似度 > 0.7（使用用户数据集）**
- ✅ 后端执行向量检索，找到相关列
- ✅ 生成 DuckDB SQL 查询
- ✅ 查询用户上传的 Parquet 文件
- ✅ 返回图表数据，`data_source: "user_dataset"`
- ✅ 前端展示图表

**方案 B: 向量相似度 < 0.7（回退到固定Schema）**
- ⚠️ 后端未找到高相似度列
- ✅ 回退到固定数据库查询
- ✅ 返回图表数据，`data_source: "fixed_schema"`

---

### 测试用例 4: 上传 Excel 文件

#### 4.1 准备测试数据

创建 `test_users.xlsx` (使用 Excel):
| 用户ID | 姓名 | 年龄 | 城市 |
|--------|------|------|------|
| 1001 | 张三 | 28 | 北京 |
| 1002 | 李四 | 35 | 上海 |
| 1003 | 王五 | 42 | 广州 |

#### 4.2 执行上传
1. 点击 📎 图标
2. 选择 `test_users.xlsx`
3. 数据集名称："用户数据测试"
4. 描述："测试用户信息"
5. 上传

#### 4.3 预期结果
- ✅ Excel 文件成功解析
- ✅ 数据集列表显示 2 个数据集
- ✅ 徽章显示 "2"

---

### 测试用例 5: 删除数据集

#### 5.1 删除操作
1. 打开数据集列表
2. 点击某个数据集的 "⋮" 菜单
3. 选择"删除"
4. 确认删除

#### 5.2 预期结果
- ✅ 弹出确认提示
- ✅ 确认后数据集从列表消失
- ✅ 徽章数字减 1
- ✅ PostgreSQL 中记录被删除
- ✅ MinIO 中文件被删除
- ✅ Qdrant 中向量被删除

---

### 测试用例 6: 文件验证

#### 6.1 上传超大文件
1. 尝试上传 > 100MB 的文件
2. **预期**: 显示错误 "文件大小不能超过 100MB"

#### 6.2 上传不支持的格式
1. 尝试上传 `.txt`, `.pdf`, `.json` 文件
2. **预期**: 显示错误 "仅支持 CSV 或 Excel 文件"

#### 6.3 空文件名
1. 清空"数据集名称"输入框
2. **预期**: "上传"按钮禁用，显示 "请输入数据集名称"

---

## 🐛 常见问题排查

### 问题 1: 上传后一直显示"解析中"

**可能原因:**
- 后台解析任务失败
- Embedding API 未配置

**排查:**
```bash
# 查看后端日志
tail -f backend/logs/app.log

# 手动检查数据集状态
curl http://127.0.0.1:11434/api/dataset/{dataset_id}/status
```

**临时解决:** Embedding 失败不影响文件解析，只是跳过向量化

---

### 问题 2: 数据集列表为空

**排查:**
```bash
# 检查 API 响应
curl http://127.0.0.1:11434/api/datasets

# 检查数据库
docker exec -it chatbi-postgres psql -U aigcgen -d chabi_template \
  -c "SELECT * FROM sys_dataset;"
```

---

### 问题 3: 前端组件未显示

**排查:**
1. 检查浏览器控制台 (F12) 是否有错误
2. 确认组件已正确导入到 `Home.vue`
3. 检查 Vuetify 自动导入是否生效

**解决:**
```bash
cd frontend
pnpm install  # 重新安装依赖
pnpm dev      # 重启开发服务器
```

---

### 问题 4: 查询未使用用户数据集

**排查:**
```bash
# 检查向量检索结果
curl -X POST http://127.0.0.1:11434/api/generate_chart \
  -H "Content-Type: application/json" \
  -d '{"user_input": "销售额最高的产品"}'

# 查看响应中的 data_source 字段
# "user_dataset" = 使用用户数据
# "fixed_schema" = 使用固定数据库
```

**可能原因:**
- 向量相似度 < 0.7 阈值
- Embedding 未生成
- 查询关键词与列名语义差距大

**解决:** 调整 `generate_chart.py:63` 的相似度阈值

---

## 📊 性能测试

### 小文件 (< 1MB, 100行)
- 上传: ~100ms
- 解析: ~200ms
- Embedding: ~1.5s
- **总计**: ~2s

### 中等文件 (10MB, 1万行)
- 上传: ~500ms
- 解析: ~2s
- Embedding: ~8s (假设20列)
- **总计**: ~11s

---

## ✅ 测试检查清单

部署测试前请确认:

- [ ] Docker 服务全部正常 (postgres, redis, minio, qdrant)
- [ ] 后端服务运行在 http://127.0.0.1:11434
- [ ] 前端服务运行在 http://localhost:3000
- [ ] MinIO Console 可访问 (http://localhost:9001)
- [ ] Qdrant Dashboard 可访问 (http://localhost:6333/dashboard)
- [ ] 环境变量已配置 (`backend/.env`)
- [ ] 数据库表已创建 (`python backend/db/init_db.py`)

---

## 🎯 下一步优化建议

### 立即可做:
1. **前端体验优化**
   - 数据集卡片样式优化
   - 上传进度动画
   - 拖拽上传支持

2. **查询增强**
   - 在输入框显示当前选中的数据集
   - 支持多数据集联合查询

### 短期优化:
3. **NL→SQL 改进**
   - 使用 LLM 生成动态 SQL（替换模板）
   - 支持复杂聚合和 JOIN

4. **错误处理**
   - 更友好的错误提示
   - 失败重试机制

### 中期优化:
5. **数据质量**
   - 数据预览功能
   - 列类型自动推断优化
   - 数据清洗建议

6. **性能优化**
   - 大文件分块上传
   - Embedding 批处理
   - 查询结果缓存

---

## 📝 API 端点总结

| 端点 | 方法 | 功能 |
|-----|------|-----|
| `/api/upload_dataset` | POST | 上传文件 |
| `/api/dataset/{id}/status` | GET | 查询解析状态 |
| `/api/datasets` | GET | 获取数据集列表 |
| `/api/dataset/{id}` | DELETE | 删除数据集 |
| `/api/generate_chart` | POST | 生成图表（支持动态数据集） |

---

**测试完成后请反馈:**
- ✅ 哪些功能正常
- ❌ 遇到什么问题
- 💡 有什么改进建议

祝测试顺利！🚀
