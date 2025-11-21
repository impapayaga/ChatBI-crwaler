@echo off
echo ========================================
echo    Docker镜像导出脚本
echo ========================================
echo.

echo 正在导出镜像为.tar文件...
echo.

echo [1/3] 导出ChatBI后端镜像...
docker save chatbi-backend:latest -o chatbi-backend.tar
if %errorlevel% neq 0 (
    echo ❌ 导出失败！
    pause
    exit /b 1
)
echo ✅ ChatBI后端镜像已导出

echo.
echo [2/2] 导出ChatBI前端镜像...
docker save chatbi-frontend:latest -o chatbi-frontend.tar
if %errorlevel% neq 0 (
    echo ❌ 导出失败！
    pause
    exit /b 1
)
echo ✅ ChatBI前端镜像已导出

REM 注意：Crawler后端镜像已禁用（生产环境不使用爬虫功能）
REM 如需启用，取消下面的注释：
REM echo.
REM echo [3/3] 导出Crawler后端镜像...
REM docker save crawler-backend:latest -o crawler-backend.tar
REM if %errorlevel% neq 0 (
REM     echo ❌ 导出失败！
REM     pause
REM     exit /b 1
REM )
REM echo ✅ Crawler后端镜像已导出

echo.
echo ========================================
echo    镜像导出完成！
echo ========================================
echo.
echo 导出的文件：
dir *.tar
echo.
echo 文件位置：%CD%
echo.
echo 下一步：将这两个.tar文件上传到服务器
echo.
pause

