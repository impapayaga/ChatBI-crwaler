@echo off
echo ========================================
echo Qdrant连接诊断工具
echo ========================================
echo.

echo [1] 检查Docker容器状态...
docker ps --filter "name=chatbi-qdrant"
echo.

echo [2] 检查Qdrant日志（最后20行）...
docker logs chatbi-qdrant --tail 20
echo.

echo [3] 测试Qdrant API连接...
curl -s http://localhost:6333/collections 2>nul
if %errorlevel% equ 0 (
    echo ✅ API连接成功！
) else (
    echo ❌ API连接失败！
)
echo.

echo [4] 检查端口占用...
netstat -ano | findstr :6333
echo.

echo [5] 尝试访问Dashboard...
echo 请在浏览器中访问: http://localhost:6333/dashboard
echo.

echo ========================================
echo 诊断完成
echo ========================================
pause


