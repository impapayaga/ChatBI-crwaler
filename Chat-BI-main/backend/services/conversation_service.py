"""
对话消息持久化服务
管理用户对话会话和消息的存储
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from models.sys_conversation import SysConversation, SysConversationMessage, MessageRoleEnum
from typing import Optional, Dict, Any
import logging
import json
import aiohttp

logger = logging.getLogger(__name__)


async def get_or_create_conversation(
    session: AsyncSession,
    user_id: int = 1,  # 默认用户ID,后续可从认证token获取
    title: str = None
) -> SysConversation:
    """
    获取或创建对话会话

    Args:
        session: 数据库会话
        user_id: 用户ID
        title: 会话标题(可选)

    Returns:
        对话会话对象
    """
    try:
        # 尝试获取用户最新的会话
        result = await session.execute(
            select(SysConversation)
            .where(SysConversation.user_id == user_id)
            .order_by(SysConversation.updated_at.desc())
            .limit(1)
        )
        conversation = result.scalar_one_or_none()

        # 如果没有会话或最后一个会话已经有很多消息,创建新会话
        if not conversation or conversation.message_count > 50:
            conversation = SysConversation(
                user_id=user_id,
                title=title or "新对话",
                message_count=0
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            logger.info(f"创建新对话会话: {conversation.id}")

        return conversation

    except Exception as e:
        logger.error(f"获取或创建对话会话失败: {e}")
        raise


async def save_message(
    session: AsyncSession,
    conversation_id: int,
    role: MessageRoleEnum,
    content: str,
    chart_data: Dict[str, Any] = None,
    chart_type: str = None,
    tokens_used: int = None,
    response_time: int = None
) -> SysConversationMessage:
    """
    保存对话消息到数据库

    Args:
        session: 数据库会话
        conversation_id: 对话会话ID
        role: 消息角色(user/assistant)
        content: 消息内容
        chart_data: 图表数据(JSON对象)
        chart_type: 图表类型
        tokens_used: 使用的token数量
        response_time: 响应时间(毫秒)

    Returns:
        保存的消息对象
    """
    try:
        # 创建消息记录
        message = SysConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            chart_data=json.dumps(chart_data, ensure_ascii=False) if chart_data else None,
            chart_type=chart_type,
            tokens_used=tokens_used,
            response_time=response_time
        )
        session.add(message)

        # 更新会话的消息计数和更新时间
        await session.execute(
            update(SysConversation)
            .where(SysConversation.id == conversation_id)
            .values(
                message_count=SysConversation.message_count + 1,
                updated_at=func.now()
            )
        )

        await session.commit()
        await session.refresh(message)

        logger.info(f"消息已保存: conversation_id={conversation_id}, role={role}, message_id={message.id}")
        return message

    except Exception as e:
        logger.error(f"保存消息失败: {e}")
        await session.rollback()
        raise


async def save_user_message(
    session: AsyncSession,
    user_input: str,
    user_id: int = 1
) -> tuple[SysConversation, SysConversationMessage]:
    """
    保存用户消息(便捷方法)

    Args:
        session: 数据库会话
        user_input: 用户输入
        user_id: 用户ID

    Returns:
        (对话会话, 用户消息)
    """
    conversation = await get_or_create_conversation(session, user_id)
    user_message = await save_message(
        session,
        conversation.id,
        MessageRoleEnum.USER,
        user_input
    )
    return conversation, user_message


async def save_assistant_message(
    session: AsyncSession,
    conversation_id: int,
    content: str,
    chart_data: Dict[str, Any] = None,
    chart_type: str = None,
    response_time: int = None,
    tokens_used: int = None
) -> SysConversationMessage:
    """
    保存AI助手回复消息(便捷方法)

    Args:
        session: 数据库会话
        conversation_id: 对话会话ID
        content: 回复内容
        chart_data: 图表数据
        chart_type: 图表类型
        response_time: 响应时间(毫秒)
        tokens_used: 使用的token数量

    Returns:
        助手消息对象
    """
    return await save_message(
        session,
        conversation_id,
        MessageRoleEnum.ASSISTANT,
        content,
        chart_data=chart_data,
        chart_type=chart_type,
        response_time=response_time,
        tokens_used=tokens_used
    )


async def get_conversation_history(
    session: AsyncSession,
    conversation_id: int,
    limit: int = 50
) -> list[SysConversationMessage]:
    """
    获取对话历史记录

    Args:
        session: 数据库会话
        conversation_id: 对话会话ID
        limit: 返回消息数量限制

    Returns:
        消息列表(按时间倒序)
    """
    try:
        result = await session.execute(
            select(SysConversationMessage)
            .where(SysConversationMessage.conversation_id == conversation_id)
            .order_by(SysConversationMessage.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(messages))  # 反转为正序

    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        return []


async def save_error_message(
    session: AsyncSession,
    conversation_id: int,
    error_message: str,
    user_input: str = None
) -> SysConversationMessage:
    """
    保存错误消息到数据库

    Args:
        session: 数据库会话
        conversation_id: 对话会话ID
        error_message: 错误信息
        user_input: 用户输入(可选)

    Returns:
        助手消息对象
    """
    content = f"抱歉,处理您的请求时出现错误: {error_message}"
    if user_input:
        content = f"针对您的问题「{user_input}」,{content}"

    return await save_message(
        session,
        conversation_id,
        MessageRoleEnum.ASSISTANT,
        content
    )


async def generate_conversation_summary(
    session: AsyncSession,
    conversation_id: int,
    user_question: str,
    assistant_response: str,
    previous_summary: str = None,
    model_config: Dict[str, Any] = None
) -> Optional[str]:
    """
    使用AI生成或更新会话摘要

    Args:
        session: 数据库会话
        conversation_id: 对话会话ID
        user_question: 用户问题
        assistant_response: AI回复
        previous_summary: 上一轮的摘要（如果有）
        model_config: AI模型配置

    Returns:
        生成的摘要文本（限制在合理长度内）
    """
    try:
        if not model_config:
            # 没有AI配置，使用简单的文本拼接
            if previous_summary:
                # 增量更新：截取上一轮摘要 + 当前问题概要
                truncated_previous = previous_summary[:300] if len(previous_summary) > 300 else previous_summary
                new_summary = f"{truncated_previous}\n→ {user_question[:100]}"
            else:
                # 初次摘要：用户问题
                new_summary = f"{user_question[:200]}"

            # 限制总长度在500字符以内
            return new_summary[:500] if len(new_summary) > 500 else new_summary

        # 使用AI生成摘要
        if previous_summary:
            # 增量更新摘要
            system_prompt = (
                "你是一个会话摘要助手。根据之前的摘要和当前对话，生成更新后的摘要。\n"
                "要求：\n"
                "1. 摘要长度不超过500个字符\n"
                "2. 保留关键信息和主要讨论点\n"
                "3. 简洁清晰，使用中文\n"
                "4. 直接返回摘要内容，不要有任何说明\n\n"
                f"之前的摘要：{previous_summary}\n\n"
                f"当前对话：\n用户：{user_question}\nAI：{assistant_response[:300]}...\n\n"
                "请生成更新后的摘要："
            )
        else:
            # 初次生成摘要
            system_prompt = (
                "你是一个会话摘要助手。根据用户问题和AI回复，生成简洁的会话摘要。\n"
                "要求：\n"
                "1. 摘要长度不超过500个字符\n"
                "2. 准确概括对话的核心内容\n"
                "3. 简洁清晰，使用中文\n"
                "4. 直接返回摘要内容，不要有任何说明\n\n"
                f"用户问题：{user_question}\n"
                f"AI回复：{assistant_response[:300]}...\n\n"
                "请生成摘要："
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model_config.get('api_key', '')}",
        }

        data = {
            "model": model_config.get('model_name', ''),
            "messages": [{"role": "system", "content": system_prompt}],
            "temperature": 0.5,
            "max_tokens": 300,
        }

        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as http_session:
            async with http_session.post(
                model_config.get('api_url', ''),
                json=data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    generated_summary = result['choices'][0]['message']['content'].strip()
                    # 限制长度
                    if len(generated_summary) > 500:
                        generated_summary = generated_summary[:500] + "..."
                    return generated_summary
                else:
                    logger.warning(f"AI摘要生成失败: {response.status}")
                    # 降级处理
                    if previous_summary:
                        return f"{previous_summary[:400]}\n→ {user_question[:100]}"[:500]
                    else:
                        return user_question[:500]

    except Exception as e:
        logger.error(f"生成会话摘要失败: {e}")
        # 降级处理
        if previous_summary:
            return f"{previous_summary[:400]}\n→ {user_question[:100]}"[:500]
        else:
            return user_question[:500]


async def update_conversation_summary(
    session: AsyncSession,
    conversation_id: int,
    user_question: str,
    assistant_response: str,
    model_config: Dict[str, Any] = None
) -> None:
    """
    更新会话摘要（异步调用AI生成摘要并更新到数据库）

    Args:
        session: 数据库会话
        conversation_id: 对话会话ID
        user_question: 用户问题
        assistant_response: AI回复
        model_config: AI模型配置
    """
    try:
        # 获取当前会话
        conv_result = await session.execute(
            select(SysConversation).where(SysConversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            logger.warning(f"会话 {conversation_id} 不存在，无法更新摘要")
            return

        # 生成新摘要
        new_summary = await generate_conversation_summary(
            session,
            conversation_id,
            user_question,
            assistant_response,
            previous_summary=conversation.summary,
            model_config=model_config
        )

        # 更新会话摘要
        if new_summary:
            conversation.summary = new_summary
            await session.commit()
            logger.info(f"会话 {conversation_id} 摘要已更新: {new_summary[:100]}...")

    except Exception as e:
        logger.error(f"更新会话摘要失败: {e}")
        await session.rollback()
