# 数据库模型说明

## 模型文件结构

```
backend/models/
├── __init__.py              # 模型导出
├── base.py                  # SQLAlchemy Base 定义
├── sys_user.py              # 系统用户表
├── sys_ai_model_config.py   # AI模型配置表
└── sys_conversation.py      # 对话会话和消息表
```

## 数据表说明

### 1. sys_user (系统用户表)

用于存储系统用户信息。

**字段说明:**
- `id`: 用户ID (主键，自增)
- `username`: 用户名 (唯一，必填，索引)
- `email`: 邮箱 (唯一，必填，索引)
- `password_hash`: 密码哈希 (必填)
- `full_name`: 全名
- `avatar_url`: 头像URL
- `is_active`: 是否激活 (默认 True)
- `is_superuser`: 是否超级管理员 (默认 False)
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 2. sys_ai_model_config (AI模型配置表)

用于存储用户的AI模型配置信息。

**字段说明:**
- `id`: 配置ID (主键，自增)
- `user_id`: 用户ID (外键，关联 sys_user.id，级联删除)
- `config_name`: 配置名称 (必填)
- `model_name`: 模型名称 (必填)
- `model_type`: 模型类型 (必填，如: chat/generate/embedding)
- `api_url`: API地址 (必填)
- `api_key`: API密钥
- `model_params`: 模型参数 (JSON格式)
- `temperature`: 温度参数 (默认 '0.7')
- `max_tokens`: 最大token数
- `description`: 配置描述
- `is_default`: 是否默认配置 (默认 False)
- `is_active`: 是否启用 (默认 True)
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 3. sys_conversation (对话会话表)

用于存储用户的对话会话信息。

**字段说明:**
- `id`: 会话ID (主键，自增)
- `user_id`: 用户ID (外键，关联 sys_user.id，级联删除)
- `title`: 会话标题
- `summary`: 会话摘要
- `message_count`: 消息数量 (默认 0)
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 4. sys_conversation_message (对话消息表)

用于存储对话会话中的消息内容。

**字段说明:**
- `id`: 消息ID (主键，自增)
- `conversation_id`: 会话ID (外键，关联 sys_conversation.id，级联删除)
- `role`: 消息角色 (枚举: user/assistant/system)
- `content`: 消息内容 (必填)
- `chart_data`: 图表数据 (JSON字符串)
- `chart_type`: 图表类型 (bar/line/pie/doughnut)
- `tokens_used`: 使用的token数量
- `response_time`: 响应时间 (毫秒)
- `created_at`: 创建时间

## 数据库初始化

### 方式1: 应用启动时自动初始化

应用启动时会自动执行以下操作：
1. 创建所有数据表
2. 插入默认管理员账户 (username: admin, password: admin123)

```bash
python main.py
```

### 方式2: 手动重置数据库

如果需要重置数据库（删除所有表并重新创建），可以使用重置脚本：

```bash
python reset_db.py
```

**警告**: 此操作会删除所有现有数据！

## 默认账户

系统会自动创建一个默认管理员账户：

- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@chatbi.com
- **权限**: 超级管理员

首次使用后请及时修改密码！

## 表关系

```
sys_user (用户)
    ├── 1:N → sys_ai_model_config (AI配置)
    └── 1:N → sys_conversation (会话)
              └── 1:N → sys_conversation_message (消息)
```

## 注意事项

1. 所有外键都设置了 `CASCADE DELETE`，删除父记录时会自动删除关联的子记录
2. 所有表都使用了时区感知的时间戳 (`DateTime(timezone=True)`)
3. 用户名和邮箱字段都添加了唯一索引和数据库索引
4. 密码使用 bcrypt 算法进行哈希存储，不存储明文密码
