# Embedding 模型配置 - 快速开始

## 🚀 5分钟快速配置指南

### 前提条件
- ✅ 后端服务已启动 (运行在 http://127.0.0.1:11434)
- ✅ 前端服务已启动 (运行在 http://localhost:3000)
- ✅ 已获取 API Key (硅基流动/OpenAI/Deepseek)

### 步骤 1: 进入配置页面

访问前端页面，进入 **AI 模型配置** 页面

### 步骤 2: 新增 Embedding 模型

点击 **"新增配置"** 按钮，填写以下信息：

#### 示例 1: 硅基流动 - BGE 中文向量模型

```
配置名称: BGE 中文 1024 维
模型类型: 嵌入模型 (Embedding)
选择提供商: 硅基流动 (SiliconFlow)
  → API 地址自动填充为: https://api.siliconflow.cn/v1/embeddings
API Key: sk-xxxxxxxxxxxxxx (填入你的硅基流动 API Key)
模型名称: BAAI/bge-large-zh-v1.5
配置描述: 中文文本向量化模型，1024 维度
```

#### 示例 2: OpenAI - 高性价比英文向量模型

```
配置名称: OpenAI Text Embedding Small
模型类型: 嵌入模型 (Embedding)
选择提供商: OpenAI
  → API 地址自动填充为: https://api.openai.com/v1/embeddings
API Key: sk-xxxxxxxxxxxxxx (填入你的 OpenAI API Key)
模型名称: text-embedding-3-small
配置描述: OpenAI 高性价比向量模型，1536 维度
```

### 步骤 3: 测试连接

1. 展开 **"测试配置"** 面板
2. 测试消息已自动填充为: `测试 Embedding 向量生成`
3. 点击 **"测试连接"** 按钮
4. 等待测试结果

**成功示例：**
```
✓ 连接成功
消息: Embedding 模型连接测试成功
响应: 生成了 1024 维的向量表示
响应时间: 823 ms
```

### 步骤 4: 保存配置

测试通过后，**"保存配置"** 按钮会自动启用，点击保存即可。

---

## 📋 常用模型推荐

### 中文场景

| 提供商 | 模型名称 | 维度 | 适用场景 |
|--------|---------|------|---------|
| 硅基流动 | `BAAI/bge-large-zh-v1.5` | 1024 | 中文语义搜索、文档检索 |
| 硅基流动 | `BAAI/bge-base-zh-v1.5` | 768 | 中文轻量级应用 |
| 硅基流动 | `BAAI/bge-m3` | 1024 | 多语言混合场景 |

### 英文场景

| 提供商 | 模型名称 | 维度 | 适用场景 |
|--------|---------|------|---------|
| OpenAI | `text-embedding-3-small` | 1536 | 高性价比通用场景 |
| OpenAI | `text-embedding-3-large` | 3072 | 高精度应用 |
| 硅基流动 | `sentence-transformers/all-MiniLM-L6-v2` | 384 | 轻量级英文应用 |

---

## ⚠️ 重要提示

### 1. 必须先测试才能保存
系统会强制要求测试通过后才能保存配置，这样可以避免保存错误的配置。

### 2. API 地址的区别

**Chat 模型:**
```
https://api.siliconflow.cn/v1/chat/completions
```

**Embedding 模型:**
```
https://api.siliconflow.cn/v1/embeddings  ← 注意是 /embeddings
```

### 3. 请求格式的区别

**Chat 请求:**
```json
{
  "model": "Qwen/Qwen2.5-72B-Instruct",
  "messages": [{"role": "user", "content": "你好"}],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Embedding 请求:**
```json
{
  "model": "BAAI/bge-large-zh-v1.5",
  "input": "测试文本"
}
```

### 4. Embedding 模型没有 Temperature 和 Max Tokens

当你选择 **"嵌入模型 (Embedding)"** 类型时，表单会自动隐藏这两个参数，因为 Embedding 模型不需要它们。

---

## 🐛 常见问题

### Q1: 测试失败 - "响应格式异常：缺少 data 字段"

**原因**: API URL 可能配置错误

**解决方案**:
- 检查 API URL 是否为 `/v1/embeddings`
- 确保没有误用 Chat API 的 URL `/v1/chat/completions`

### Q2: 测试失败 - "HTTP 401: Unauthorized"

**原因**: API Key 无效或没有权限

**解决方案**:
- 验证 API Key 是否正确
- 检查 API Key 是否有 Embedding API 的访问权限
- 确认账户余额是否充足

### Q3: 保存按钮一直是灰色的

**原因**: 测试未通过或未进行测试

**解决方案**:
- 展开"测试配置"面板
- 点击"测试连接"并等待测试通过
- 测试成功后保存按钮会自动启用

### Q4: 切换模型类型后，提供商的 API 地址没变

**原因**: 需要重新选择提供商

**解决方案**:
- 切换模型类型后，重新在"选择提供商"下拉框中选择提供商
- API 地址会自动更新为对应类型的端点

---

## 🧪 测试命令 (可选)

如果你想直接测试后端 API，可以使用 curl：

### 测试 Embedding 模型

```bash
curl -X POST "http://127.0.0.1:11434/api/ai-model-configs/test" \
  -H "Content-Type: application/json" \
  -d '{
    "api_url": "https://api.siliconflow.cn/v1/embeddings",
    "api_key": "sk-your-api-key",
    "model_name": "BAAI/bge-large-zh-v1.5",
    "model_type": "embedding",
    "test_message": "测试 Embedding 向量生成"
  }'
```

### 测试 Chat 模型 (对比)

```bash
curl -X POST "http://127.0.0.1:11434/api/ai-model-configs/test" \
  -H "Content-Type: application/json" \
  -d '{
    "api_url": "https://api.siliconflow.cn/v1/chat/completions",
    "api_key": "sk-your-api-key",
    "model_name": "Qwen/Qwen2.5-72B-Instruct",
    "model_type": "chat",
    "temperature": 0.7,
    "max_tokens": 2000,
    "test_message": "你好"
  }'
```

---

## 📚 更多信息

详细的 API 说明和技术实现请参考: [EMBEDDING_MODEL_GUIDE.md](./EMBEDDING_MODEL_GUIDE.md)
