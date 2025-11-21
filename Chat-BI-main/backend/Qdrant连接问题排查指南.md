# Qdrant连接问题排查指南

## 🔍 问题现象

**警告和错误**：
```
UserWarning: Failed to obtain server version. Unable to check client-server compatibility.
WARNING: Qdrant连接失败（尝试 1/3），1秒后重试: Unexpected Response: 502 (Bad Gateway)
ERROR: 检查/创建维度化Qdrant collection失败（已重试3次）: Unexpected Response: 502 (Bad Gateway)
```

## 🎯 可能原因

### 1. Qdrant服务未完全启动
- Docker容器刚启动，但服务还在初始化
- 健康检查未通过

### 2. 网络连接问题
- 端口映射问题
- 防火墙阻止
- Docker网络配置问题

### 3. Qdrant服务崩溃
- 内存不足
- 配置错误
- 数据损坏

## ✅ 排查步骤

### 步骤1：检查Qdrant容器状态

```bash
# 检查容器是否运行
docker ps | grep qdrant

# 应该看到类似输出：
# chatbi-qdrant    Up   0.0.0.0:6333->6333/tcp, 0.0.0.0:6334->6334/tcp
```

### 步骤2：检查Qdrant服务日志

```bash
# 查看容器日志
docker logs chatbi-qdrant --tail 50

# 查看是否有错误信息
docker logs chatbi-qdrant 2>&1 | grep -i error
```

### 步骤3：测试Qdrant API连接

```bash
# 测试HTTP API
curl http://localhost:6333/collections

# 应该返回JSON响应，包含collections列表
# 如果返回502，说明服务确实不可用
```

### 步骤4：检查端口占用

```bash
# Windows
netstat -ano | findstr :6333

# 应该看到类似：
# TCP    0.0.0.0:6333    0.0.0.0:0    LISTENING    12345
```

### 步骤5：检查Qdrant Dashboard

浏览器访问：http://localhost:6333/dashboard

- 如果无法访问，说明服务未启动
- 如果能看到Dashboard，说明服务正常

## 🔧 解决方案

### 方案1：重启Qdrant服务

```bash
# 停止并重新启动
docker-compose -f backend/docker-compose.yml down
docker-compose -f backend/docker-compose.yml up -d qdrant

# 等待几秒让服务完全启动
sleep 5

# 检查日志确认启动成功
docker logs chatbi-qdrant --tail 20
```

### 方案2：检查并修复配置

**检查URL配置**：
```python
# backend/core/config.py
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
```

**检查环境变量**：
```bash
# 在backend目录下
cat .env | grep QDRANT
# 应该看到：
# QDRANT_URL=http://localhost:6333
```

### 方案3：添加健康检查等待

如果Qdrant启动慢，可以在代码中添加等待逻辑：

```python
import time

def wait_for_qdrant(max_wait=30):
    """等待Qdrant服务就绪"""
    for i in range(max_wait):
        if _check_qdrant_health():
            return True
        time.sleep(1)
    return False
```

### 方案4：检查Docker网络

```bash
# 检查Docker网络
docker network ls

# 如果Qdrant在Docker网络中，可能需要使用容器名而非localhost
# 例如：http://chatbi-qdrant:6333
```

## 📋 已实现的改进

### 1. 禁用版本检查警告
```python
qdrant_client = QdrantClient(url=settings.QDRANT_URL, check_compatibility=False)
```

### 2. 添加健康检查函数
```python
def _check_qdrant_health() -> bool:
    """检查Qdrant服务健康状态"""
    try:
        qdrant_client.get_collections()
        return True
    except:
        return False
```

### 3. 重试机制
- 自动重试3次
- 指数退避（2秒、4秒）
- 详细的错误日志

## 🚀 快速诊断命令

```bash
# 一键检查所有服务状态
echo "=== Docker容器状态 ==="
docker ps --filter "name=chatbi-"

echo "=== Qdrant日志（最后20行） ==="
docker logs chatbi-qdrant --tail 20

echo "=== 测试Qdrant API ==="
curl -s http://localhost:6333/collections | head -20

echo "=== 端口占用情况 ==="
netstat -ano | findstr :6333
```

## 🎯 常见问题

### Q1: Qdrant容器显示为Up，但API返回502

**可能原因**：
- 服务还在初始化（等待几秒）
- 服务崩溃但容器未退出
- 端口映射问题

**解决方案**：
```bash
# 重启容器
docker restart chatbi-qdrant

# 等待5-10秒后测试
curl http://localhost:6333/collections
```

### Q2: 初始化警告但不影响功能

**警告**：`Failed to obtain server version`

**解决方案**：
- 已添加 `check_compatibility=False` 参数
- 这个警告不影响功能，可以忽略

### Q3: 重试3次后仍然失败

**可能原因**：
- Qdrant服务确实不可用
- 网络配置问题
- 端口被占用

**解决方案**：
1. 检查Qdrant服务状态
2. 检查日志：`docker logs chatbi-qdrant`
3. 重启服务：`docker restart chatbi-qdrant`

## 📝 检查清单

- [ ] Qdrant容器是否运行？`docker ps | grep qdrant`
- [ ] 端口6333是否开放？`netstat -ano | findstr :6333`
- [ ] API是否可访问？`curl http://localhost:6333/collections`
- [ ] Dashboard是否可访问？http://localhost:6333/dashboard
- [ ] 日志是否有错误？`docker logs chatbi-qdrant | grep -i error`
- [ ] URL配置是否正确？`echo $QDRANT_URL` 或检查 `.env` 文件

## 💡 建议

1. **启动顺序**：先启动Docker服务（Qdrant），再启动后端服务
2. **等待时间**：Qdrant启动可能需要5-10秒，不要立即测试
3. **监控日志**：使用 `docker logs -f chatbi-qdrant` 实时监控
4. **健康检查**：在docker-compose中添加healthcheck（可选）







