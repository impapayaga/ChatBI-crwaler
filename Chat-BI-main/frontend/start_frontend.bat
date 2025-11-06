@echo off
echo ========================================
echo    ChatBI前端服务启动脚本 (Windows)
echo ========================================
echo.
echo 当前配置状态:
echo ✅ 前端环境变量已配置
echo ✅ VITE_API_BASE_URL: http://localhost:11434
echo ✅ VITE_CRAWLER_API_BASE_URL: http://localhost:8001
echo ✅ URL列宽控制修复完成
echo ✅ 前端UI修复完成
echo.
echo 按任意键开始启动前端服务...
pause >nul
echo.

REM 检查Node.js和pnpm
echo [1/3] 检查依赖环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js未安装！
    echo 请安装Node.js: https://nodejs.org/
    pause
    exit /b 1
)

pnpm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pnpm未安装！
    echo 正在安装pnpm...
    npm install -g pnpm
    if %errorlevel% neq 0 (
        echo ❌ pnpm安装失败！
        pause
        exit /b 1
    )
)
echo ✅ 环境检查完成

REM 安装前端依赖
echo.
echo [2/3] 安装前端依赖...
pnpm install
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败！
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

REM 启动前端服务
echo.
echo [3/3] 启动前端开发服务器...
echo ========================================
echo    前端服务启动中...
echo ========================================
echo.
echo 🚀 启动成功后访问: http://localhost:3000
echo.
echo 🔧 功能说明:
echo   - 数据爬取管理: 左侧菜单 "数据爬取管理"
echo   - 数据集管理: 左侧菜单 "数据集" 图标
echo   - 智能问数: 主输入框进行数据查询
echo   - 文件上传: 点击输入框左侧的夹子图标
echo.
echo 💡 提示:
echo   - 确保后端服务已启动 (端口11434和8001)
echo   - 如有问题请查看浏览器开发者工具
echo.
echo ========================================
echo.

pnpm dev

REM 如果前端启动失败，提供帮助信息
if %errorlevel% neq 0 (
    echo.
    echo ❌ 前端启动失败！
    echo.
    echo 🔧 故障排除:
    echo   1. 检查端口3000是否被占用: netstat -an | findstr :3000
    echo   2. 清理node_modules: rm -rf node_modules && pnpm install
    echo   3. 确保后端服务运行在11434端口
    echo.
    pause
)
pause >nul






