#!/bin/bash

# ChatBI 服务启动脚本
# 用于快速启动所有依赖服务和应用

set -e

echo "======================================"
echo "ChatBI 服务启动脚本"
echo "======================================"
echo ""

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 步骤 1: 启动 Docker 服务
echo "📦 步骤 1/4: 启动 Docker 服务..."
cd backend
docker-compose up -d

echo "⏳ 等待服务就绪..."
sleep 5

# 检查服务状态
echo ""
echo "🔍 检查服务状态:"
docker-compose ps

# 步骤 2: 检查数据库连接
echo ""
echo "🗄️  步骤 2/4: 检查数据库连接..."
until docker exec chatbi-postgres pg_isready -U aigcgen -d chabi_template > /dev/null 2>&1; do
    echo "等待 PostgreSQL 就绪..."
    sleep 2
done
echo "✅ PostgreSQL 已就绪"

# 步骤 3: 初始化数据库（如果需要）
echo ""
echo "🔧 步骤 3/4: 初始化数据库..."
if command -v python &> /dev/null; then
    echo "运行数据库初始化脚本..."
    python db/init_db.py
    echo "✅ 数据库初始化完成"
else
    echo "⚠️  Python 未安装，跳过数据库初始化"
    echo "   请手动运行: python backend/db/init_db.py"
fi

# 步骤 4: 显示访问地址
echo ""
echo "======================================"
echo "✅ 服务启动完成！"
echo "======================================"
echo ""
echo "📍 服务访问地址:"
echo "  - PostgreSQL:  localhost:5433"
echo "  - Redis:       localhost:6388"
echo "  - MinIO API:   http://localhost:9000"
echo "  - MinIO UI:    http://localhost:9001"
echo "    (登录: minioadmin / minioadmin123)"
echo "  - Qdrant API:  http://localhost:6333"
echo "  - Qdrant UI:   http://localhost:6333/dashboard"
echo ""
echo "📝 下一步操作:"
echo "  1. 启动后端服务:"
echo "     cd backend && python main.py"
echo ""
echo "  2. 启动前端服务 (另开终端):"
echo "     cd frontend && pnpm dev"
echo ""
echo "  3. 访问应用:"
echo "     http://localhost:3000"
echo ""
echo "======================================"
echo ""
echo "💡 提示:"
echo "  - 查看测试指南: cat TEST_INTEGRATION.md"
echo "  - 停止服务: cd backend && docker-compose down"
echo "  - 查看日志: docker-compose logs -f"
echo ""
