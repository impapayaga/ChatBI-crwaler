@echo off
echo 政策文件爬取与AI总结系统
echo ================================

echo 正在安装依赖包...
pip install -r requirements.txt

echo.
echo 选择运行模式:
echo 1. 启动API服务 (默认)
echo 2. 启动定时任务
echo 3. 立即执行一次爬取和总结
echo 4. 打开模拟前端
echo.

set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" (
    echo 启动API服务...
    python main.py --mode api
) else if "%choice%"=="2" (
    echo 启动定时任务...
    python main.py --mode scheduler
) else if "%choice%"=="3" (
    echo 立即执行一次任务...
    python main.py --mode run_once
) else if "%choice%"=="4" (
    echo 打开模拟前端...
    start demo_frontend.html
    echo 请确保API服务已启动 (选择1)
) else (
    echo 无效选择，启动API服务...
    python main.py --mode api
)

pause
