# Embedding 模型配置指南

## 概述

本系统现已支持 Embedding 模型的配置和测试。Embedding 模型用于将文本转换为向量表示，常用于：
- 语义搜索
- 文本相似度计算
- 文档检索
- 推荐系统

## 功能特性

### 1. 自动化测试验证
- **必须测试通过才能保存**：在保存配置前，系统会强制要求进行连接测试
- **不同模型类型的测试逻辑**：
  - Chat/Generate 模型：测试对话响应
  - Embedding 模型：测试向量生成

### 2. 模型类型支持
- **对话模型 (Chat)**：用于聊天对话
- **生成模型 (Generate)**：用于文本生成
- **嵌入模型 (Embedding)**：用于文本向量化

### 3. 动态表单
- 当选择 Embedding 模型时：
  - 隐藏 Temperature 和 Max Tokens 参数（Embedding 模型不需要）
  - 显示 Embedding 模型说明
  - 自动更新测试消息为适合 Embedding 的内容
  - 提供商选项自动切换为 Embedding API 端点

## 支持的提供商

### 硅基流动 (SiliconFlow)
- **Chat API**: `https://api.siliconflow.cn/v1/chat/completions`
  - 推荐模型: `Qwen/Qwen2.5-72B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`
- **Embedding API**: `https://api.siliconflow.cn/v1/embeddings`
  - 推荐模型:
    - `BAAI/bge-large-zh-v1.5` (中文 1024 维)
    - `BAAI/bge-base-zh-v1.5` (中文 768 维)
    - `BAAI/bge-m3` (多语言 1024 维)
    - `sentence-transformers/all-MiniLM-L6-v2` (英文 384 维)

### OpenAI
- **Chat API**: `https://api.openai.com/v1/chat/completions`
  - 推荐模型: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`
- **Embedding API**: `https://api.openai.com/v1/embeddings`
  - 推荐模型:
    - `text-embedding-3-small` (1536 维，性价比高)
    - `text-embedding-3-large` (3072 维，高精度)
    - `text-embedding-ada-002` (1536 维，传统版本)

### Deepseek
- **Chat API**: `https://api.deepseek.com/v1/chat/completions`
  - 推荐模型: `deepseek-chat`, `deepseek-coder`
- **Embedding API**: `https://api.deepseek.com/v1/embeddings`
  - 推荐模型: `deepseek-embeddings` (根据官方文档确认)

## 使用步骤

### 1. 添加 Embedding 模型配置

1. 进入 AI 模型配置页面
2. 点击"新增配置"
3. 填写配置信息：
   - **配置名称**：例如 "BGE 中文向量模型"
   - **模型类型**：选择 "嵌入模型 (Embedding)"
   - **选择提供商**：选择一个提供商（例如"硅基流动"）
     - API 地址会自动填充为对应的 Embedding 端点
   - **API Key**：输入你的 API Key
   - **API 地址**：已自动填充，如需修改可手动编辑
   - **模型名称**：**需手动输入**，参考提示中的推荐模型
     - 硅基流动示例: `BAAI/bge-large-zh-v1.5`
     - OpenAI 示例: `text-embedding-3-small`

### 2. 测试连接

1. 展开"测试配置"面板
2. 测试消息会自动设置为 "测试 Embedding 向量生成"
3. 点击"测试连接"按钮
4. 等待测试结果：
   - ✓ **成功**：显示生成的向量维度（例如："生成了 1024 维的向量表示"）
   - ✗ **失败**：显示错误信息和详情

### 3. 保存配置

- **测试通过后**，"保存配置"按钮会启用
- 如果未测试或测试失败，按钮会保持禁用状态，并提示先测试

## API 端点说明

### 后端测试接口

**POST** `/api/ai-model-configs/test`

**参数**：
```
api_url: str          # API 地址
api_key: str          # API 密钥
model_name: str       # 模型名称
model_type: str       # 模型类型 (chat/generate/embedding)
temperature: float    # 温度参数（仅 chat/generate）
max_tokens: int       # 最大 token 数（仅 chat/generate）
test_message: str     # 测试消息
```

**Chat/Generate 请求体**：
```json
{
  "model": "model_name",
  "messages": [
    {
      "role": "user",
      "content": "test_message"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Embedding 请求体**：
```json
{
  "model": "model_name",
  "input": "test_message",
  "encoding_format": "float"
}
```

**响应格式**：
```json
{
  "success": true,
  "responseTime": 1250,
  "message": "Embedding 模型连接测试成功",
  "response": "生成了 1024 维的向量表示"
}
```

## 测试示例

### 测试硅基流动 Embedding 模型

```bash
curl -X POST "http://127.0.0.1:11434/api/ai-model-configs/test" \
  -H "Content-Type: application/json" \
  -d '{
    "api_url": "https://api.siliconflow.cn/v1/embeddings",
    "api_key": "your_api_key_here",
    "model_name": "BAAI/bge-large-zh-v1.5",
    "model_type": "embedding",
    "test_message": "测试 Embedding 向量生成"
  }'
```

### 预期响应

```json
{
  "success": true,
  "responseTime": 823,
  "message": "Embedding 模型连接测试成功",
  "response": "生成了 1024 维的向量表示"
}
```

## 故障排除

### 1. 测试失败：响应格式异常

**问题**：API 返回的数据格式不符合预期

**解决方案**：
- 检查 API URL 是否正确（应为 `/v1/embeddings` 而非 `/v1/chat/completions`）
- 确认模型名称是否支持 Embedding
- 查看详细错误信息

### 2. 测试失败：HTTP 401

**问题**：API Key 无效或过期

**解决方案**：
- 验证 API Key 是否正确
- 检查 API Key 是否有 Embedding API 的访问权限
- 联系提供商确认账户状态

### 3. 测试失败：网络超时

**问题**：请求超过 30 秒未响应

**解决方案**：
- 检查网络连接
- 确认 API 地址可访问
- 尝试使用其他网络环境

## 技术实现细节

### 后端实现 (backend/api/endpoints/ai_model_config.py)

- 根据 `model_type` 参数构建不同的请求体
- Embedding 模型使用 `input` 字段而非 `messages`
- 验证返回的向量数据格式和维度
- 返回向量维度信息供用户确认

### 前端实现 (frontend/src/components/AIModelConfigDialog.vue)

- 使用 `computed` 属性动态切换提供商选项
- 监听模型类型变化，自动更新 UI 和测试消息
- 条件渲染：Embedding 模型隐藏不相关参数
- 保存前验证：必须有成功的测试结果

## 数据库 Schema

Embedding 模型配置存储在 `sys_ai_model_config` 表中：

```sql
CREATE TABLE sys_ai_model_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- 'chat', 'generate', 'embedding'
    api_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(255),
    model_params JSON,
    temperature VARCHAR(10) DEFAULT '0.7',
    max_tokens INTEGER,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 最佳实践

1. **命名规范**：使用清晰的配置名称，例如 "BGE 中文 1024维"
2. **测试消息**：使用有代表性的文本进行测试
3. **API Key 安全**：妥善保管 API Key，不要提交到版本控制
4. **模型选择**：根据实际需求选择合适维度的 Embedding 模型
5. **定期测试**：定期验证已保存的配置是否仍然有效

## 未来扩展

- [ ] 批量向量生成测试
- [ ] 向量相似度计算演示
- [ ] Embedding 模型性能对比
- [ ] 自动推荐最佳 Embedding 模型
- [ ] 向量数据库集成
