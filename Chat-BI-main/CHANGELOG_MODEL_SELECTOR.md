# 模型选择器优化 - 更新日志

## 修改日期
2025-01-XX

## 修改内容

### 前端优化 - ModelSelector.vue

**问题描述:**
模型选择下拉框显示了所有类型的模型（chat、generate、embedding），但聊天界面应该只能选择对话模型。

**优化方案:**
在 `ModelSelector.vue` 的 `fetchModels` 函数中添加过滤逻辑，只显示 `modelType === 'chat'` 的模型。

**修改位置:**
`frontend/src/components/ModelSelector.vue:117-127`

**修改前:**
```typescript
models.value = items
  .filter((m: any) => m.isActive === true || m.is_active === true)
  .map((m: any) => ({
    // ... 映射逻辑
  }))
```

**修改后:**
```typescript
models.value = items
  // 只显示激活的且模型类型为 chat 的模型
  .filter((m: any) => {
    const isActive = m.isActive === true || m.is_active === true
    const modelType = (m.modelType || m.model_type || '').toLowerCase()
    const isChatModel = modelType === 'chat'
    if (!isChatModel) {
      console.log(`过滤掉非chat模型: ${m.configName || m.config_name} (类型: ${modelType})`)
    }
    return isActive && isChatModel
  })
  .map((m: any) => ({
    // ... 映射逻辑
  }))
```

## 效果

### 修改前
- ✗ 显示所有类型的模型（chat、generate、embedding）
- ✗ 用户可能误选择非对话类型的模型
- ✗ 可能导致聊天功能异常

### 修改后
- ✓ **只显示 chat 类型的模型**
- ✓ 自动过滤掉 generate 和 embedding 类型的模型
- ✓ 控制台会输出被过滤掉的模型信息，方便调试
- ✓ 避免用户误选择错误的模型类型

## 技术细节

### 过滤条件
1. **激活状态**: `isActive === true`
2. **模型类型**: `modelType === 'chat'` (不区分大小写)

### 兼容性处理
- 支持驼峰命名: `modelType`
- 支持下划线命名: `model_type`
- 自动转换为小写进行比较

### 调试日志
```
总模型数: 5
过滤掉非chat模型: BGE 中文向量模型 (类型: embedding)
过滤掉非chat模型: OpenAI Embedding (类型: embedding)
过滤后的 Chat 模型数量: 3
Chat 模型列表: [...]
```

## 相关文件

- `frontend/src/components/ModelSelector.vue` - 模型选择器组件
- `backend/models/sys_ai_model_config.py` - 模型配置数据模型
- `backend/api/endpoints/ai_model_config.py` - 模型配置 API

## 测试建议

### 测试步骤
1. 启动前后端服务
2. 在 AI 模型配置页面添加不同类型的模型:
   - Chat 模型 (如: `Qwen/Qwen2.5-72B-Instruct`)
   - Embedding 模型 (如: `BAAI/bge-large-zh-v1.5`)
   - Generate 模型 (如有)
3. 返回聊天界面
4. 点击模型选择器下拉框
5. **验证**: 只能看到 Chat 类型的模型

### 预期结果
- ✓ 下拉框只显示 chat 类型的模型
- ✓ Embedding 模型不会出现在列表中
- ✓ Generate 模型不会出现在列表中
- ✓ 如果没有 chat 模型，显示"无可用模型"

## 未来优化建议

1. **类型常量化**: 将模型类型定义为枚举或常量
   ```typescript
   enum ModelType {
     CHAT = 'chat',
     GENERATE = 'generate',
     EMBEDDING = 'embedding'
   }
   ```

2. **配置化过滤**: 允许不同组件指定需要的模型类型
   ```typescript
   interface ModelSelectorProps {
     allowedTypes?: ModelType[]
   }
   ```

3. **图标优化**: 为不同模型类型显示不同的图标
   ```typescript
   const getModelIcon = (modelType: string): string => {
     const iconMap: Record<string, string> = {
       'chat': 'mdi-message-text',
       'embedding': 'mdi-vector-combine',
       'generate': 'mdi-text-box-multiple'
     }
     return iconMap[modelType] || 'mdi-robot'
   }
   ```

4. **性能优化**: 如果模型数量很大，考虑添加虚拟滚动

## 影响范围

- ✅ 前端: `ModelSelector.vue` 组件
- ✅ 用户体验: 防止误选错误类型的模型
- ✅ 调试: 增加了过滤日志
- ⬜ 后端: 无影响
- ⬜ 数据库: 无影响

## 版本信息

- 修改版本: v1.1.0
- 兼容性: 向后兼容
- 破坏性变更: 无
