#!/usr/bin/env python3
"""
测试 Embedding 模型配置功能

使用方法:
    python test_embedding.py

注意: 需要先启动后端服务 (python main.py)
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# 配置
BASE_URL = "http://127.0.0.1:11434"
API_KEY = "your_api_key_here"  # 请替换为实际的 API Key


async def test_embedding_model(
    api_url: str,
    api_key: str,
    model_name: str,
    test_message: str = "测试 Embedding 向量生成"
) -> Dict[str, Any]:
    """测试 Embedding 模型"""

    test_url = f"{BASE_URL}/api/ai-model-configs/test"

    params = {
        "api_url": api_url,
        "api_key": api_key,
        "model_name": model_name,
        "model_type": "embedding",
        "test_message": test_message
    }

    print(f"\n{'='*60}")
    print(f"测试 Embedding 模型: {model_name}")
    print(f"API URL: {api_url}")
    print(f"测试消息: {test_message}")
    print(f"{'='*60}\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(test_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()

                    print(f"✓ 测试结果: {'成功' if result.get('success') else '失败'}")
                    print(f"  消息: {result.get('message')}")

                    if result.get('response'):
                        print(f"  响应: {result.get('response')}")

                    if result.get('responseTime'):
                        print(f"  响应时间: {result.get('responseTime')} ms")

                    if result.get('details'):
                        print(f"  详情: {result.get('details')}")

                    return result
                else:
                    error_text = await response.text()
                    print(f"✗ HTTP 错误 {response.status}: {error_text}")
                    return {"success": False, "message": f"HTTP {response.status}"}

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return {"success": False, "message": str(e)}


async def test_chat_model(
    api_url: str,
    api_key: str,
    model_name: str,
    test_message: str = "你好，请介绍一下你自己。"
) -> Dict[str, Any]:
    """测试 Chat 模型（用于对比）"""

    test_url = f"{BASE_URL}/api/ai-model-configs/test"

    params = {
        "api_url": api_url,
        "api_key": api_key,
        "model_name": model_name,
        "model_type": "chat",
        "temperature": 0.7,
        "max_tokens": 2000,
        "test_message": test_message
    }

    print(f"\n{'='*60}")
    print(f"测试 Chat 模型: {model_name}")
    print(f"API URL: {api_url}")
    print(f"测试消息: {test_message}")
    print(f"{'='*60}\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(test_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()

                    print(f"✓ 测试结果: {'成功' if result.get('success') else '失败'}")
                    print(f"  消息: {result.get('message')}")

                    if result.get('response'):
                        print(f"  响应: {result.get('response')[:100]}...")

                    if result.get('responseTime'):
                        print(f"  响应时间: {result.get('responseTime')} ms")

                    return result
                else:
                    error_text = await response.text()
                    print(f"✗ HTTP 错误 {response.status}: {error_text}")
                    return {"success": False, "message": f"HTTP {response.status}"}

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return {"success": False, "message": str(e)}


async def main():
    """主测试函数"""

    print("\n" + "="*60)
    print("ChatBI Embedding 模型测试")
    print("="*60)

    # 测试配置列表
    test_configs = [
        {
            "type": "embedding",
            "name": "硅基流动 BGE",
            "api_url": "https://api.siliconflow.cn/v1/embeddings",
            "model_name": "BAAI/bge-large-zh-v1.5",
            "test_message": "测试中文文本向量化"
        },
        {
            "type": "embedding",
            "name": "OpenAI Embedding",
            "api_url": "https://api.openai.com/v1/embeddings",
            "model_name": "text-embedding-3-small",
            "test_message": "Test English text embedding"
        },
        {
            "type": "chat",
            "name": "硅基流动 Qwen",
            "api_url": "https://api.siliconflow.cn/v1/chat/completions",
            "model_name": "Qwen/Qwen2.5-72B-Instruct",
            "test_message": "你好，请简单介绍一下你自己。"
        }
    ]

    results = []

    for config in test_configs:
        if API_KEY == "your_api_key_here":
            print(f"\n⚠ 跳过 {config['name']}: 请先配置 API Key")
            continue

        try:
            if config["type"] == "embedding":
                result = await test_embedding_model(
                    api_url=config["api_url"],
                    api_key=API_KEY,
                    model_name=config["model_name"],
                    test_message=config["test_message"]
                )
            else:
                result = await test_chat_model(
                    api_url=config["api_url"],
                    api_key=API_KEY,
                    model_name=config["model_name"],
                    test_message=config["test_message"]
                )

            results.append({
                "name": config["name"],
                "type": config["type"],
                "success": result.get("success", False)
            })

        except Exception as e:
            print(f"✗ 测试 {config['name']} 时出错: {str(e)}")
            results.append({
                "name": config["name"],
                "type": config["type"],
                "success": False
            })

        # 等待一下，避免请求过快
        await asyncio.sleep(1)

    # 打印汇总
    print(f"\n{'='*60}")
    print("测试汇总")
    print(f"{'='*60}\n")

    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)

    for result in results:
        status = "✓" if result["success"] else "✗"
        print(f"{status} {result['name']} ({result['type']})")

    print(f"\n通过: {success_count}/{total_count}")

    if API_KEY == "your_api_key_here":
        print("\n⚠ 提示: 请在脚本中配置实际的 API Key 以运行完整测试")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试失败: {str(e)}")
