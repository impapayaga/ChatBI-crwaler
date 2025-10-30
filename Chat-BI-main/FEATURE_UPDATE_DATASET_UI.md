# ChatBI 前端功能更新 - 数据集选择UI优化

**更新日期**: 2025-10-18
**版本**: v1.2.0

---

## 🎯 本次更新概览

优化数据集选择和显示功能,提供更直观的用户体验:

1. ✅ **前端支持 .et 文件格式**
2. ✅ **输入框上方显示选中的数据集标签**
3. ✅ **支持多数据集选择**
4. ✅ **水平滚动查看多个数据集**
5. ✅ **一键移除选中的数据集**

---

## 📋 功能详情

### 1. 前端支持 .et 文件格式

**修改文件**: `frontend/src/components/FileUploadDialog.vue`

**更新内容**:
- 文件选择器接受 `.et` 扩展名
- 文件验证规则包含 `.et` 格式
- 提示文本更新为 "支持 CSV、Excel、WPS 表格文件"

**代码改动**:
```vue
<!-- 更新前 -->
<v-file-input
  accept=".csv,.xlsx,.xls"
  hint="支持 CSV、Excel 文件，最大 100MB"
/>

<!-- 更新后 -->
<v-file-input
  accept=".csv,.xlsx,.xls,.et"
  hint="支持 CSV、Excel、WPS 表格文件，最大 100MB"
/>
```

---

### 2. 数据集标签组件

**新增文件**: `frontend/src/components/DatasetChips.vue`

**功能特性**:
- 🏷️ 卡片式标签显示选中的数据集
- ℹ️ 鼠标悬停显示完整信息(文件名、行列数)
- ❌ 一键移除功能
- 📜 水平滚动支持多个数据集
- 🎨 与 Vuetify 主题集成

**组件结构**:
```vue
<DatasetChips
  :datasets="selectedDatasets"
  @remove="handleRemoveDataset"
/>
```

**标签信息显示**:
- 主标题: 数据集逻辑名称
- Tooltip:
  - 完整名称
  - 原始文件名
  - 数据规模 (行 × 列)
  - 移除提示

**样式特点**:
```css
/* 半透明背景 */
background-color: rgba(var(--v-theme-surface-variant), 0.3);

/* 水平滚动,自动隐藏滚动条 */
overflow-x: auto;
scrollbar-width: thin;

/* 深色模式适配 */
:global(.v-theme--dark) .dataset-chips-container {
  background-color: rgba(var(--v-theme-surface-variant), 0.15);
}
```

---

### 3. ChatInput 集成数据集显示

**修改文件**: `frontend/src/components/ChatInput.vue`

**更新内容**:

#### 3.1 Props 新增
```typescript
interface Props {
  // ... 其他props
  selectedDatasets?: Dataset[]  // 新增
}
```

#### 3.2 Emits 新增
```typescript
interface Emits {
  // ... 其他emits
  (e: 'removeDataset', datasetId: string): void  // 新增
}
```

#### 3.3 布局调整
```vue
<div class="chat-input-container">
  <!-- 数据集标签区域 (新增) -->
  <DatasetChips
    v-if="selectedDatasets.length > 0"
    :datasets="selectedDatasets"
    @remove="handleRemoveDataset"
  />

  <!-- 输入框 -->
  <div
    class="chat-input-wrapper"
    :class="{
      'focused': isFocused,
      'has-datasets': selectedDatasets.length > 0  // 新增class
    }">
    <!-- 输入区域 -->
  </div>
</div>
```

#### 3.4 样式优化
```css
/* 有数据集时,输入框顶部圆角改为0,与标签区域无缝衔接 */
.chat-input-wrapper.has-datasets {
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}
```

**视觉效果**:
```
┌────────────────────────────────────┐
│ 📊 已选择: [数据集1] [数据集2] ... │  ← 标签区域 (8px圆角顶部)
├────────────────────────────────────┤
│ 请输入问题...                      │  ← 输入框 (0圆角顶部)
│                                    │
│ 📎 [工具] ... [发送]               │
└────────────────────────────────────┘  (24px圆角底部)
```

---

### 4. Home.vue 数据集管理

**修改文件**: `frontend/src/components/Home.vue`

#### 4.1 状态管理
```typescript
// 更新前
const selectedDatasetId = ref<string | null>(null)

// 更新后 - 支持多选
const selectedDatasets = ref<Dataset[]>([])

interface Dataset {
  id: string
  name: string
  logical_name?: string
  row_count: number
  column_count: number
}
```

#### 4.2 数据集选择逻辑
```typescript
// 支持多选,防止重复
const handleDatasetSelect = (dataset: Dataset) => {
  const index = selectedDatasets.value.findIndex(d => d.id === dataset.id)
  if (index === -1) {
    // 未选中,添加到列表
    selectedDatasets.value.push(dataset)
  } else {
    // 已选中,不重复添加
    console.log('数据集已在选中列表中')
  }
}
```

#### 4.3 移除数据集
```typescript
const handleRemoveDataset = (datasetId: string) => {
  selectedDatasets.value = selectedDatasets.value.filter(d => d.id !== datasetId)
}
```

#### 4.4 上传成功自动添加
```typescript
const handleUploadSuccess = async (datasetId: string) => {
  // 刷新数据集列表
  if (datasetListRef.value) {
    datasetListRef.value.refreshDatasets()
  }

  // 获取数据集详情并自动添加到选中列表
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${datasetId}/status`
    )
    const dataset = response.data
    handleDatasetSelect({
      id: dataset.dataset_id,
      name: dataset.name,
      logical_name: dataset.logical_name,
      row_count: dataset.row_count || 0,
      column_count: dataset.column_count || 0
    })
  } catch (error) {
    console.error('获取数据集详情失败:', error)
  }
}
```

#### 4.5 传递数据集到输入框
```vue
<!-- 初始状态 -->
<ChatInput
  v-model="inputValue"
  :selected-datasets="selectedDatasets"
  @remove-dataset="handleRemoveDataset"
  <!-- 其他props -->
/>

<!-- 对话状态 -->
<ChatInput
  v-model="inputValue"
  :selected-datasets="selectedDatasets"
  @remove-dataset="handleRemoveDataset"
  <!-- 其他props -->
/>
```

---

## 🎨 用户体验流程

### 完整流程示例

1. **上传数据集**
   ```
   用户点击 📎 → 选择文件 → 上传
   ↓
   上传成功 → 自动添加到选中列表
   ↓
   输入框上方显示数据集标签
   ```

2. **手动选择数据集**
   ```
   用户点击 🗄️ 数据集列表 → 选择数据集
   ↓
   检查是否重复 → 添加到选中列表
   ↓
   输入框上方显示新标签
   ```

3. **查看数据集信息**
   ```
   鼠标悬停在标签上
   ↓
   Tooltip显示:
   - 数据集名称
   - 原始文件名
   - 数据规模 (行×列)
   - 移除提示
   ```

4. **移除数据集**
   ```
   点击标签上的 ❌
   ↓
   从选中列表移除
   ↓
   标签消失
   ```

5. **多数据集滚动**
   ```
   选中多个数据集
   ↓
   标签超出输入框宽度
   ↓
   自动启用水平滚动
   ↓
   用户左右拖动查看所有数据集
   ```

---

## 📊 组件间数据流

```
DatasetList (数据集列表)
    ↓ @select-dataset
Home.vue
    ↓ handleDatasetSelect()
selectedDatasets (ref)
    ↓ :selected-datasets prop
ChatInput
    ↓ prop drilling
DatasetChips
    ↓ @remove
ChatInput
    ↓ @remove-dataset emit
Home.vue
    ↓ handleRemoveDataset()
selectedDatasets (过滤移除)
```

---

## 🎯 视觉对比

### 更新前
```
┌──────────────────────────┐
│ 请输入问题...            │
│                          │
│ 📎 [工具] ... [发送]     │
└──────────────────────────┘

❌ 无法看到选中了哪些数据集
❌ 无法快速移除数据集
❌ 不支持多数据集选择
```

### 更新后
```
┌─────────────────────────────────────────┐
│ 📊 已选择: [销售数据] [用户数据] ...   │  ← 标签区域
├─────────────────────────────────────────┤
│ 请输入问题...                           │  ← 输入框
│                                         │
│ 📎 [工具] ... [发送]                    │
└─────────────────────────────────────────┘

✅ 清晰显示所有选中的数据集
✅ 一键移除功能
✅ 支持多数据集选择
✅ 水平滚动查看
✅ Tooltip 详细信息
```

---

## 🔧 配置说明

### 无需额外配置
所有功能开箱即用,无需修改环境变量或配置文件。

### 样式定制
如需自定义样式,修改以下文件:
- `DatasetChips.vue` - 标签样式
- `ChatInput.vue` - 输入框与标签衔接

---

## 🧪 测试建议

### 1. 测试 .et 文件上传
```
1. 准备 WPS 表格文件 (.et)
2. 点击上传按钮
3. 选择 .et 文件
4. 验证文件被接受
5. 验证解析成功
```

### 2. 测试数据集标签显示
```
1. 上传一个数据集
2. 验证输入框上方显示标签
3. 验证标签显示数据集名称
4. 鼠标悬停验证 Tooltip
```

### 3. 测试多数据集选择
```
1. 上传/选择多个数据集
2. 验证所有数据集都显示为标签
3. 验证标签水平排列
4. 验证可以水平滚动
```

### 4. 测试移除功能
```
1. 选择多个数据集
2. 点击某个标签的 ❌
3. 验证该数据集被移除
4. 验证其他数据集保留
```

### 5. 测试重复选择
```
1. 选择一个数据集
2. 再次选择相同数据集
3. 验证不会重复添加
4. 验证控制台输出提示
```

---

## 📁 修改文件清单

**新增文件**:
1. `frontend/src/components/DatasetChips.vue` - 数据集标签组件

**修改文件**:
1. `frontend/src/components/FileUploadDialog.vue` - 添加 .et 支持
2. `frontend/src/components/ChatInput.vue` - 集成标签显示
3. `frontend/src/components/Home.vue` - 多数据集管理

---

## 🚀 下一步建议

1. **后端API扩展** - 支持在查询时指定使用哪些数据集
2. **数据集预览** - 点击标签显示数据集预览
3. **数据集排序** - 拖拽调整数据集优先级
4. **持久化选择** - 记住用户上次选择的数据集
5. **数据集分组** - 支持创建数据集集合/工作区

---

## 📸 效果预览

### 单个数据集
```
┌───────────────────────────────────┐
│ 📊 已选择: [销售数据] ×           │
├───────────────────────────────────┤
│ 分析销售数据的数据...             │
│ 📎 [工具] ... [发送]              │
└───────────────────────────────────┘
```

### 多个数据集
```
┌─────────────────────────────────────────────────┐
│ 📊 已选择: [销售数据] [用户数据] [订单数据] ... │  ← 可滚动
├─────────────────────────────────────────────────┤
│ 请输入问题...                                   │
│ 📎 [工具] ... [发送]                            │
└─────────────────────────────────────────────────┘
```

### Tooltip 显示
```
  ┌─ [销售数据] ×
  │    ↑
  │    └─ 鼠标悬停
  │
  └─→ Tooltip:
      ┌─────────────────────┐
      │ 销售数据            │
      │ 📄 test_sales.csv   │
      │ 📊 50 行 × 4 列     │
      │ 点击 × 移除         │
      └─────────────────────┘
```

---

## ✨ 总结

本次更新实现了您要求的所有前端功能:

1. ✅ **前端支持 .et 文件** - 文件选择器和验证规则已更新
2. ✅ **输入框上方显示数据集** - 类似附件的标签展示
3. ✅ **水平滚动支持** - 多个数据集时自动启用滚动
4. ✅ **一键移除** - 点击 × 快速移除数据集
5. ✅ **多数据集管理** - 支持同时选择多个数据集
6. ✅ **自动添加** - 上传成功后自动加入选中列表
7. ✅ **防重复** - 智能检测避免重复添加

### 用户价值
- 🎯 **直观明了** - 一眼看到选中的数据集
- ⚡ **快速操作** - 一键添加/移除
- 📊 **详细信息** - Tooltip 显示完整信息
- 🎨 **美观大方** - 与整体UI风格一致
- 📱 **响应式设计** - 适配不同屏幕尺寸

---

**开发者**: Claude Code
**审核**: 待用户确认
**部署**: 已在开发环境部署,前端组件已更新
