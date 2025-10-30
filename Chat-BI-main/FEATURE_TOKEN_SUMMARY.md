# Token记录和会话摘要功能实现文档

## 功能概述

本次更新实现了两个核心功能:
1. **Token使用量记录**: 记录每条AI消息使用的token数量
2. **会话摘要自动生成**: 每轮对话后自动生成和更新会话摘要

## 1. Token使用量记录

### 数据库字段

在 `sys_conversation_message` 表中:
- `tokens_used` (Integer): 记录该消息使用的token总数
- `response_time` (Integer): 记录响应时间(毫秒)

### 实现位置

#### 流式API (`insight_analysis_stream.py`)
```python
# 行173-175: 定义token计数变量
tokens_used = None  # 记录token使用量
prompt_tokens = 0  # 提示词token数
completion_tokens = 0  # 生成token数

# 行323-330: 从流式响应中提取token使用量
if "usage" in chunk_data:
    usage_data = chunk_data["usage"]
    prompt_tokens = usage_data.get("prompt_tokens", 0)
    completion_tokens = usage_data.get("completion_tokens", 0)
    tokens_used = usage_data.get("total_tokens") or (prompt_tokens + completion_tokens)

# 行344: 保存消息时记录token
await save_assistant_message(
    db,
    conversation_id,
    content=full_content,
    response_time=response_time,
    tokens_used=tokens_used  # 记录token使用量
)
```

#### 非流式API (`ai_utils.py`)
```python
# 行203: 添加return_usage参数
async def call_configured_ai_model(
    system_prompt,
    user_input=None,
    user_id: int = 1,
    return_usage: bool = False  # 新增参数
):
    # 行247-254: 提取并返回token信息
    if return_usage:
        usage = result.get('usage', {})
        token_info = {
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }
        return content, token_info
```

## 2. 会话摘要自动生成

### 数据库字段

在 `sys_conversation` 表中:
- `summary` (Text): 会话摘要内容(限制500字符)

### 摘要生成逻辑

#### 初次摘要
当会话第一次有用户问题和AI回复时:
- 使用用户问题 + AI回复内容
- 调用AI模型生成简洁摘要(≤500字符)
- 如果没有AI配置,使用用户问题的前200字符

#### 增量更新
后续每轮对话完成后:
- 使用上一轮摘要 + 当前用户问题 + 当前AI回复
- 调用AI模型生成更新后的摘要
- 覆盖原有摘要内容

### 实现位置

#### 摘要生成服务 (`conversation_service.py`)

```python
# 行245-350: generate_conversation_summary函数
async def generate_conversation_summary(
    session: AsyncSession,
    conversation_id: int,
    user_question: str,
    assistant_response: str,
    previous_summary: str = None,
    model_config: Dict[str, Any] = None
) -> Optional[str]:
    """
    生成或更新会话摘要
    - 初次: 使用用户问题+AI回复
    - 增量: 使用上一轮摘要+当前对话
    - 长度限制: 500字符
    """
```

```python
# 行352-399: update_conversation_summary函数
async def update_conversation_summary(
    session: AsyncSession,
    conversation_id: int,
    user_question: str,
    assistant_response: str,
    model_config: Dict[str, Any] = None
) -> None:
    """
    更新会话摘要并保存到数据库
    """
```

#### 集成位置

##### 流式分析端点 (`insight_analysis_stream.py`)
```python
# 行360-362: 每轮流式对话完成后异步更新摘要
asyncio.create_task(
    update_summary_async(conversation_id, request.user_input, full_content)
)
```

##### 图表生成端点 (`generate_chart.py`)
```python
# 行285-290: 生成图表后也更新摘要
background_tasks.add_task(
    update_summary_for_conversation,
    conversation_id,
    user_input.user_input,
    assistant_content
)
```

## 3. 测试验证

运行测试脚本:
```bash
cd backend
python test_token_and_summary.py
```

### 测试覆盖
1. ✅ Token记录功能验证
2. ✅ 摘要初次生成验证
3. ✅ 摘要增量更新验证
4. ✅ 完整对话流程验证
5. ✅ 数据库表结构验证

## 4. API响应格式变化

### 查询对话消息API
`GET /api/conversation/{conversation_id}/messages`

响应中每条消息现在包含:
```json
{
  "id": 1,
  "role": "assistant",
  "content": "...",
  "created_at": "2024-01-01T00:00:00Z",
  "response_time": 1200,  // 响应时间(毫秒)
  "tokens_used": 150      // Token使用量
}
```

### 查询对话列表API
`GET /api/conversations/{user_id}`

响应中每个对话现在包含:
```json
{
  "id": 1,
  "title": "数据分析对话",
  "message_count": 10,
  "summary": "讨论了2024年销售数据趋势...",  // 会话摘要(新增)
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T01:00:00Z"
}
```

## 5. 性能优化

### 异步处理
- 摘要生成使用后台任务(`background_tasks`)或异步任务(`asyncio.create_task`)
- 不阻塞主要的API响应流程

### 降级策略
- 如果AI模型调用失败,摘要生成会使用简单的文本拼接作为fallback
- Token记录失败不影响消息保存

## 6. 注意事项

1. **Token统计准确性**:
   - 流式API的token统计依赖于API提供商在响应中返回`usage`字段
   - 某些API可能不提供token信息,此时`tokens_used`为`None`

2. **摘要长度控制**:
   - AI生成的摘要会被截断到500字符
   - 增量更新时会优先保留最新的对话内容

3. **数据库迁移**:
   - 如果是从旧版本升级,需要确保数据库表包含新字段
   - 运行 `python init_db.py` 会自动创建/更新表结构

4. **AI配置依赖**:
   - 摘要生成需要用户配置AI模型
   - 如果没有配置,会使用简单的文本截取作为摘要

## 7. 后续优化建议

1. **Token成本统计**: 添加token成本计算(基于不同模型的价格)
2. **摘要质量优化**: 对摘要提示词进行A/B测试
3. **历史摘要管理**: 保留摘要变更历史,支持回溯
4. **多语言支持**: 摘要生成支持自动检测语言
5. **用户自定义**: 允许用户手动编辑摘要

## 8. 相关文件清单

### 修改的文件
- `backend/api/endpoints/insight_analysis_stream.py` - 流式API token记录
- `backend/api/endpoints/generate_chart.py` - 图表生成摘要集成
- `backend/api/utils/ai_utils.py` - 非流式API token支持
- `backend/services/conversation_service.py` - 摘要生成逻辑(已存在,本次验证)

### 新增的文件
- `backend/test_token_and_summary.py` - 功能测试脚本
- `FEATURE_TOKEN_SUMMARY.md` - 本文档

### 数据库表
- `sys_conversation` - 添加`summary`字段
- `sys_conversation_message` - 添加`tokens_used`和`response_time`字段
