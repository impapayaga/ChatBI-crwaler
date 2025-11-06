@echo off
echo ========================================
echo    ChatBI完整服务启动脚本
echo ========================================
echo.

echo [1/4] 启动Docker服务...
cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\backend
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ Docker服务启动失败！
    pause
    exit /b 1
)
echo ✅ Docker服务启动成功

echo.
echo [2/4] 启动ChatBI后端服务...
start "ChatBI Backend" cmd /k "cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\backend && conda activate chatbi && set PYTHONPATH=C:\Users\KC\Desktop\POC\Chat-BI-main\backend && echo 启动ChatBI后端服务... && python main.py"
timeout /t 3 /nobreak >nul

echo.
echo [3/4] 启动Crawler适配服务...
start "Crawler Backend" cmd /k "cd /d C:\Users\KC\Desktop\POC\crawler+AI-summarizer && echo 启动Crawler适配服务... && python adapter_api.py"
timeout /t 3 /nobreak >nul

echo.
echo [4/4] 启动ChatBI前端服务...
start "ChatBI Frontend" cmd /k "cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\frontend && echo 启动ChatBI前端服务... && pnpm dev"

echo.
echo ========================================
echo    所有服务启动完成！
echo ========================================
echo.
echo 🌐 服务访问地址:
echo   前端界面: http://localhost:3000
echo   ChatBI后端: http://localhost:11434
echo   Crawler后端: http://localhost:8001
echo.
echo 📊 管理界面:
echo   MinIO控制台: http://localhost:9001 (minioadmin/minioadmin123)
echo   Qdrant面板: http://localhost:6333/dashboard
echo.
echo 🔧 API文档:
echo   ChatBI API: http://localhost:11434/docs
echo   Crawler API: http://localhost:8001/docs
echo.
echo 按任意键退出...
pause >nul



