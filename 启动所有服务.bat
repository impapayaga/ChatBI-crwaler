@echo off
echo ========================================
echo    ChatBI完整系统一键启动
echo ========================================
echo.
echo 🚀 正在启动ChatBI完整系统...
echo.
echo [1/3] 启动后端基础设施和ChatBI服务...
start "ChatBI Backend Setup" cmd /k "cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\backend && C:\Users\KC\Desktop\POC\Chat-BI-main\backend\init_and_start.bat"

echo.
echo [2/3] 等待后端服务启动...
timeout /t 15 /nobreak >nul

echo.
echo [3/3] 启动前端服务...
start "ChatBI Frontend" cmd /k "cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\frontend && C:\Users\KC\Desktop\POC\Chat-BI-main\frontend\start_frontend.bat"

echo.
echo ========================================
echo    启动脚本执行完成！
echo ========================================
echo.
echo 🌟 服务启动状态:
echo   ✅ Docker服务正在启动...
echo   ✅ 后端服务(11434)正在启动...
echo   ✅ 爬虫服务(8001)正在启动...
echo   ✅ 前端服务(3000)正在启动...
echo.
echo 🌐 访问地址:
echo   前端界面: http://localhost:3000
echo   ChatBI API: http://localhost:11434/docs
echo   Crawler API: http://localhost:8001/docs
echo   MinIO控制台: http://localhost:9001
echo.
echo 💡 提示:
echo   - 所有服务启动需要几分钟时间
echo   - 完成后访问 http://localhost:3000
echo   - 查看左侧数据集图标，应该有3个测试数据集
echo.
echo 按任意键退出...
pause >nul
