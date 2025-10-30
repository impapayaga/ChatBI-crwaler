"""
Token记录和会话摘要功能使用示例

演示如何在代码中使用新功能
"""
import asyncio
from sqlalchemy import select
from db.session import async_session
from models.sys_conversation import SysConversation, SysConversationMessage
from services.conversation_service import (
    save_user_message,
    save_assistant_message,
    update_conversation_summary
)


async def example_1_save_message_with_tokens():
    """示例1: 保存带token信息的消息"""
    print("\n=== 示例1: 保存带token信息的消息 ===\n")

    async with async_session() as db:
        # 1. 保存用户消息
        conversation, user_msg = await save_user_message(
            db,
            user_input="查询2024年销售数据",
            user_id=1
        )
        print(f"✓ 保存用户消息: conversation_id={conversation.id}")

        # 2. 保存助手消息,记录token使用量
        assistant_msg = await save_assistant_message(
            db,
            conversation_id=conversation.id,
            content="已为您生成销售数据图表",
            chart_data={"data": [...], "chart_type": "bar"},  # 图表数据
            chart_type="bar",
            tokens_used=180,      # 记录token使用量
            response_time=1500    # 记录响应时间(毫秒)
        )
        print(f"✓ 保存助手消息: message_id={assistant_msg.id}")
        print(f"  - Token使用: {assistant_msg.tokens_used}")
        print(f"  - 响应时间: {assistant_msg.response_time}ms")


async def example_2_update_summary():
    """示例2: 更新会话摘要"""
    print("\n=== 示例2: 更新会话摘要 ===\n")

    async with async_session() as db:
        # 创建对话
        conversation, _ = await save_user_message(
            db,
            "介绍一下Python的特点",
            user_id=1
        )
        print(f"✓ 创建对话: conversation_id={conversation.id}")

        # 保存助手回复
        ai_response = "Python是一种高级编程语言，具有简洁的语法和强大的功能。"
        await save_assistant_message(
            db,
            conversation.id,
            content=ai_response,
            tokens_used=80
        )

        # 获取AI配置(用于生成摘要)
        from services.model_cache_service import ModelCacheService
        model_config = await ModelCacheService.get_user_selected_model(
            user_id=1,
            db=db
        )

        # 更新会话摘要
        await update_conversation_summary(
            db,
            conversation_id=conversation.id,
            user_question="介绍一下Python的特点",
            assistant_response=ai_response,
            model_config=model_config
        )
        print("✓ 会话摘要已更新")

        # 查询更新后的摘要
        result = await db.execute(
            select(SysConversation).where(SysConversation.id == conversation.id)
        )
        conv = result.scalar_one()
        print(f"  摘要内容: {conv.summary}")


async def example_3_query_with_tokens():
    """示例3: 查询消息的token使用情况"""
    print("\n=== 示例3: 查询消息的token使用情况 ===\n")

    async with async_session() as db:
        # 查询最近的助手消息
        result = await db.execute(
            select(SysConversationMessage)
            .where(SysConversationMessage.role == 'assistant')
            .order_by(SysConversationMessage.created_at.desc())
            .limit(5)
        )
        messages = result.scalars().all()

        print(f"最近5条助手消息的Token使用情况:\n")
        total_tokens = 0
        for i, msg in enumerate(messages, 1):
            tokens = msg.tokens_used or 0
            total_tokens += tokens
            print(f"{i}. 消息ID={msg.id}: {tokens} tokens, 响应时间={msg.response_time}ms")

        print(f"\n总计Token使用量: {total_tokens}")


async def example_4_conversation_analytics():
    """示例4: 对话分析 - 统计token成本"""
    print("\n=== 示例4: 对话分析 - 统计token成本 ===\n")

    async with async_session() as db:
        # 查询某个对话的所有消息
        conversation_id = 1  # 示例对话ID

        result = await db.execute(
            select(SysConversation).where(SysConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            print("对话不存在")
            return

        # 统计该对话的token使用
        result = await db.execute(
            select(SysConversationMessage).where(
                SysConversationMessage.conversation_id == conversation_id
            )
        )
        messages = result.scalars().all()

        total_tokens = sum(msg.tokens_used or 0 for msg in messages if msg.role == 'assistant')
        avg_response_time = sum(msg.response_time or 0 for msg in messages if msg.response_time) / len([m for m in messages if m.response_time]) if messages else 0

        print(f"对话ID: {conversation_id}")
        print(f"标题: {conversation.title}")
        print(f"摘要: {conversation.summary}")
        print(f"消息数量: {conversation.message_count}")
        print(f"总Token使用: {total_tokens}")
        print(f"平均响应时间: {avg_response_time:.0f}ms")

        # 按token成本计算(假设价格)
        # 示例: $0.002 per 1K tokens
        cost_per_1k = 0.002
        estimated_cost = (total_tokens / 1000) * cost_per_1k
        print(f"预估成本: ${estimated_cost:.4f}")


async def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("Token记录和会话摘要功能使用示例".center(60))
    print("="*60)

    # 运行示例
    await example_1_save_message_with_tokens()
    await example_2_update_summary()
    await example_3_query_with_tokens()
    await example_4_conversation_analytics()

    print("\n" + "="*60)
    print("示例运行完成!".center(60))
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
