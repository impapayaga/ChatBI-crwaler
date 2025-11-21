@echo off
echo ========================================
echo    重新构建前端镜像（使用服务器IP）
echo ========================================
echo.
echo ⚠️  此脚本用于等您有服务器地址后，重新构建前端镜像
echo.
set /p SERVER_IP="请输入服务器IP地址（例如：192.168.1.100）: "

if "%SERVER_IP%"=="" (
    echo ❌ 服务器IP不能为空！
    pause
    exit /b 1
)

echo.
echo 使用服务器IP: %SERVER_IP%
echo.

echo 正在重新构建前端镜像...
cd Chat-BI-main\frontend
REM 注意：VITE_CRAWLER_API_BASE_URL 已禁用（生产环境不使用爬虫功能）
docker build --build-arg VITE_API_BASE_URL=http://%SERVER_IP%:11434 -t chatbi-frontend:latest .

if %errorlevel% neq 0 (
    echo ❌ 构建失败！
    pause
    exit /b 1
)

echo.
echo ✅ 前端镜像重新构建成功！
echo.
echo 下一步：运行"导出镜像.bat"重新导出前端镜像
echo.
pause

