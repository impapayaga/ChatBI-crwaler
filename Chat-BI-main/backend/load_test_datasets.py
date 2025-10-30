#!/usr/bin/env python3
"""
测试数据集自动导入脚本
将test_data目录中的CSV文件自动上传到ChatBI系统
"""

import asyncio
import os
import sys
import requests
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings

# 测试数据集配置
TEST_DATASETS = [
    {
        "file": "test_sales.csv",
        "name": "销售数据测试",
        "description": "2024年销售数据测试数据集，包含日期、产品、销售额、销售数量等字段"
    },
    {
        "file": "test_orders.csv",
        "name": "订单数据测试",
        "description": "订单数据测试数据集，用于测试数据分析功能"
    },
    {
        "file": "test_users.csv",
        "name": "用户数据测试",
        "description": "用户数据测试数据集，用于测试用户行为分析"
    }
]

def upload_dataset(file_path: str, name: str, description: str) -> dict:
    """上传单个数据集"""
    try:
        # 准备文件上传请求
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/csv')}
            data = {
                'logical_name': name,
                'description': description
            }

            response = requests.post(
                f"http://localhost:{settings.FASTAPI_PORT}/api/upload_dataset",
                files=files,
                data=data,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] 上传成功: {name}")
            print(f"   文件: {file_path}")
            print(f"   数据集ID: {result.get('dataset_id')}")
            print(f"   状态: {result.get('status')}")
            return result
        else:
            print(f"[FAILED] 上传失败: {name}")
            print(f"   状态码: {response.status_code}")
            print(f"   错误: {response.text}")
            return None

    except Exception as e:
        print(f"[ERROR] 上传异常: {name}")
        print(f"   错误: {e}")
        return None

def check_dataset_status(dataset_id: str) -> dict:
    """检查数据集解析状态"""
    try:
        response = requests.get(
            f"http://localhost:{settings.FASTAPI_PORT}/api/dataset/{dataset_id}/status",
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"   状态检查失败: {response.status_code}")
            return None

    except Exception as e:
        print(f"   状态检查异常: {e}")
        return None

async def main():
    """主函数"""
    print("=" * 60)
    print("ChatBI 测试数据集自动导入")
    print("=" * 60)
    print()

    # 检查后端服务状态
    try:
        response = requests.get(f"http://localhost:{settings.FASTAPI_PORT}/api/health", timeout=5)
        print(f"[OK] 后端服务正常运行 (端口 {settings.FASTAPI_PORT})")
    except:
        print(f"[ERROR] 后端服务未运行，请先启动后端服务")
        print(f"   运行: cd backend && python main.py")
        return

    # 检查测试数据文件
    test_data_dir = project_root / "test_data"
    if not test_data_dir.exists():
        print(f"[ERROR] 测试数据目录不存在: {test_data_dir}")
        return

    print(f"[INFO] 找到测试数据目录: {test_data_dir}")
    print()

    # 上传测试数据集
    uploaded_datasets = []

    for dataset in TEST_DATASETS:
        file_path = test_data_dir / dataset["file"]

        if not file_path.exists():
            print(f"[ERROR] 测试文件不存在: {file_path}")
            continue

        print(f"[UPLOAD] 正在上传: {dataset['name']}")
        print(f"   文件路径: {file_path}")

        # 上传数据集
        result = upload_dataset(file_path, dataset["name"], dataset["description"])

        if result and result.get("dataset_id"):
            dataset_id = result["dataset_id"]
            uploaded_datasets.append((dataset_id, dataset["name"]))

            # 等待解析完成
            print(f"[WAIT] 等待数据集解析完成...")
            max_wait = 60  # 最多等待60秒
            for i in range(max_wait):
                status_result = check_dataset_status(dataset_id)

                if status_result:
                    status = status_result.get("parse_status")
                    progress = status_result.get("parse_progress", 0)

                    if status == "parsed":
                        print(f"   [SUCCESS] 解析完成! 进度: {progress}%")
                        print(f"   数据规模: {status_result.get('row_count', 0)} 行 × {status_result.get('column_count', 0)} 列")
                        break
                    elif status == "failed":
                        print(f"   [FAILED] 解析失败: {status_result.get('error_message', '未知错误')}")
                        break
                    else:
                        print(f"   [PROGRESS] 解析中... {progress}%")
                        time.sleep(2)
                else:
                    print(f"   [WAIT] 等待状态检查...")
                    time.sleep(2)

            print()
        else:
            print()

    # 总结
    print("=" * 60)
    print("导入结果总结")
    print("=" * 60)

    if uploaded_datasets:
        print(f"[SUCCESS] 成功导入 {len(uploaded_datasets)} 个测试数据集")

        # 检查最终状态
        print("\n数据集状态:")
        for dataset_id, name in uploaded_datasets:
            status_result = check_dataset_status(dataset_id)
            if status_result:
                status = status_result.get("parse_status", "unknown")
                rows = status_result.get("row_count", 0)
                cols = status_result.get("column_count", 0)
                print(f"   {name}: {status} ({rows} × {cols})")

        print("\n现在可以访问前端查看数据集管理功能了!")
        print("   前端地址: http://localhost:3000")
        print("   数据集管理: 点击左侧菜单的数据集图标")

    else:
        print("[ERROR] 没有成功导入任何测试数据集")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
