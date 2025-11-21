@echo off
echo ========================================
echo    Docker镜像构建脚本
echo ========================================
echo.

echo [1/3] 构建ChatBI后端镜像...
cd Chat-BI-main\backend
docker build -t chatbi-backend:latest .
if %errorlevel% neq 0 (
    echo ❌ ChatBI后端镜像构建失败！
    pause
    exit /b 1
)
echo ✅ ChatBI后端镜像构建成功
echo.

echo [2/2] 构建ChatBI前端镜像（使用localhost）...
REM 注意：Crawler后端镜像已禁用（生产环境不使用爬虫功能）
REM 如需启用，取消下面的注释：
REM echo [2/3] 构建Crawler后端镜像...
REM cd ..\..\crawler+AI-summarizer
REM docker build -t crawler-backend:latest .
REM if %errorlevel% neq 0 (
REM     echo ❌ Crawler后端镜像构建失败！
REM     pause
REM     exit /b 1
REM )
REM echo ✅ Crawler后端镜像构建成功
REM echo.

cd ..\Chat-BI-main\frontend
docker build --build-arg VITE_API_BASE_URL=http://localhost:11434 -t chatbi-frontend:latest .
if %errorlevel% neq 0 (
    echo ❌ ChatBI前端镜像构建失败！
    pause
    exit /b 1
)
echo ✅ ChatBI前端镜像构建成功
echo.

cd ..\..\

echo ========================================
echo    镜像构建完成！
echo ========================================
echo.
echo 已构建的镜像：
docker images | findstr -E "chatbi|crawler"
echo.
echo 下一步：运行"导出镜像.bat"导出镜像文件
echo.
pause

