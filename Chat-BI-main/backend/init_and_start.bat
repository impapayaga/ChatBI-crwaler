@echo off
echo ========================================
echo    ChatBI完整系统启动脚本 (Windows)
echo ========================================
echo.
echo 当前修复状态:
echo ✅ Redis连接修复
echo ✅ Embedding配置修复 (SiliconFlow)
echo ✅ 向量化维度修复 (1024维)
echo ✅ 测试数据集已导入
echo ✅ 前端UI修复完成
echo.
echo 按任意键开始启动服务...
pause >nul
echo.

REM 步骤 1: 启动Docker服务
echo [1/5] 启动Docker基础设施服务...
cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\backend
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ Docker服务启动失败！
    echo 请检查Docker Desktop是否运行
    pause
    exit /b 1
)
echo ✅ Docker服务启动成功

echo.
echo [2/5] 等待服务就绪...
timeout /t 10 /nobreak >nul

REM 步骤 2: 检查并初始化数据库
echo.
echo [3/5] 初始化数据库...
echo 检查数据库连接...
docker exec chatbi-postgres pg_isready -U aigcgen -d chabi_template >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 数据库连接失败！
    pause
    exit /b 1
)

echo ✅ 数据库连接正常
echo 运行数据库初始化...
python db/init_db.py
if %errorlevel% neq 0 (
    echo ❌ 数据库初始化失败！
    pause
    exit /b 1
)
echo ✅ 数据库初始化完成

REM 步骤 3: 启动ChatBI后端服务
echo.
echo [4/5] 启动ChatBI后端服务...
start "ChatBI Backend" cmd /k "cd /d C:\Users\KC\Desktop\POC\Chat-BI-main\backend && conda activate chatbi && set PYTHONPATH=C:\Users\KC\Desktop\POC\Chat-BI-main\backend && echo 启动ChatBI后端服务... && python main.py"

echo 等待后端启动...
timeout /t 5 /nobreak >nul

REM 步骤 4: 启动Crawler后端服务
echo.
echo [5/5] 启动Crawler适配服务...
start "Crawler Backend" cmd /k "cd /d C:\Users\KC\Desktop\POC\crawler+AI-summarizer && echo 启动Crawler适配服务... && python adapter_api.py"

echo 等待适配服务启动...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    后端服务启动完成！
echo ========================================
echo.
echo 🌐 后端服务地址:
echo   ChatBI后端: http://localhost:11434
echo   Crawler后端: http://localhost:8001
echo.
echo 📊 基础设施服务:
echo   PostgreSQL: localhost:5433
echo   Redis: localhost:6388
echo   MinIO API: http://localhost:9000
echo   MinIO控制台: http://localhost:9001
echo   Qdrant API: http://localhost:6333
echo.
echo 📝 API文档:
echo   ChatBI API: http://localhost:11434/docs
echo   Crawler API: http://localhost:8001/docs
echo.
echo 🔄 下一步: 启动前端服务
echo   在新的终端中运行:
echo   cd C:\Users\KC\Desktop\POC\Chat-BI-main\frontend
echo   pnpm dev
echo.
echo 🌟 前端访问: http://localhost:3000
echo.
echo 按任意键退出...
pause >nul






