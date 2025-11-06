# Qdrant代理问题修复总结

## 🔍 问题根源

**现象**：
- Qdrant服务本身正常（curl返回200 OK）
- 但Python客户端连接时返回502 Bad Gateway
- 日志显示连接经过代理（`port=7897`）

**根本原因**：
- Qdrant客户端底层使用`httpx`库
- `httpx`会自动使用系统的`HTTP_PROXY`环境变量
- 本地服务（localhost:6333）不应该使用代理
- 代理无法正确处理localhost连接，导致502错误

## ✅ 解决方案

### 核心修复

1. **检测localhost连接**：
   - 自动检测QDRANT_URL是否包含localhost、127.0.0.1等

2. **设置NO_PROXY环境变量**：
   - 将localhost添加到NO_PROXY，告诉httpx不使用代理

3. **尝试自定义httpx客户端**：
   - 如果QdrantClient支持`httpx_client`参数，使用禁用代理的客户端
   - 如果不支持，回退到NO_PROXY环境变量方式

### 实现代码

```python
# 检查是否使用localhost
is_localhost = any(host in settings.QDRANT_URL for host in ['localhost', '127.0.0.1', '0.0.0.0'])

if is_localhost:
    # 设置NO_PROXY环境变量
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1,0.0.0.0,*.local'
    
    # 尝试使用自定义httpx客户端（禁用代理）
    try:
        custom_httpx_client = httpx.Client(proxies=None)
        qdrant_client = QdrantClient(..., httpx_client=custom_httpx_client)
    except TypeError:
        # 回退到NO_PROXY方式
        qdrant_client = QdrantClient(...)
```

## 📋 修复内容

### 修改位置
- **文件**：`services/embedding_service.py` 第24-84行
- **功能**：Qdrant客户端初始化

### 修复策略
1. ✅ **自动检测**：识别localhost连接
2. ✅ **双重保护**：
   - 设置NO_PROXY环境变量
   - 尝试使用自定义httpx客户端
3. ✅ **向后兼容**：远程服务不受影响

## 🎯 效果

### 之前
- ❌ 本地连接通过代理 → 502错误
- ❌ 重试3次仍然失败

### 现在
- ✅ 本地连接绕过代理，直接连接
- ✅ 重试机制作为备用保护

## ⚠️ 注意事项

1. **NO_PROXY环境变量**：
   - 设置后会影响整个Python进程
   - 但只对localhost连接有效，不影响其他服务

2. **httpx_client参数**：
   - 如果QdrantClient版本不支持，会自动回退到NO_PROXY方式
   - 两种方式都能解决问题

3. **远程服务**：
   - 如果QDRANT_URL不是localhost，使用默认配置（可以使用代理）

## 🚀 验证

重启服务后，应该看到：
```
INFO: Qdrant客户端初始化成功（使用自定义httpx客户端，禁用代理）: http://localhost:6333
# 或
INFO: Qdrant客户端初始化成功（通过NO_PROXY禁用代理）: http://localhost:6333
```

连接应该不再经过代理，直接连接到Qdrant服务。

## 📝 额外建议

如果问题仍然存在，可以：

1. **检查系统代理设置**：
   ```powershell
   # Windows
   netsh winhttp show proxy
   ```

2. **临时禁用代理**（如果需要）：
   ```powershell
   netsh winhttp reset proxy
   ```

3. **在启动脚本中设置NO_PROXY**：
   ```bash
   set NO_PROXY=localhost,127.0.0.1,*.local
   python main.py
   ```


