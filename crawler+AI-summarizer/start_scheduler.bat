@echo off
echo 启动每周自动爬取调度器...
echo 调度器将在每周一上午9点自动执行爬取和AI总结任务
echo 按 Ctrl+C 可以停止调度器
echo.
python main.py --mode scheduler --schedule weekly
pause

