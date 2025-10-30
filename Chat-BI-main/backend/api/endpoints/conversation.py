"""
对话历史API端点
提供对话会话和消息的查询接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from api.dependencies.dependencies import get_async_session
from models.sys_conversation import SysConversation, SysConversationMessage, MessageRoleEnum
from typing import List, Optional
import logging
import json
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


class UpdateTitleRequest(BaseModel):
    """更新对话标题请求"""
    title: str


class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    user_id: int
    title: str = "新对话"


class GenerateTitleRequest(BaseModel):
    """生成会话标题请求"""
    conversation_id: int
    user_question: str


@router.post("/conversation/create")
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    创建新的对话会话

    Args:
        request: 包含user_id和title的请求
        db: 数据库会话

    Returns:
        新创建的会话ID
    """
    try:
        # 创建新会话
        new_conversation = SysConversation(
            user_id=request.user_id,
            title=request.title,
            message_count=0
        )
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)

        logger.info(f"创建新对话会话: user_id={request.user_id}, conversation_id={new_conversation.id}")

        return {
            "success": True,
            "conversation_id": new_conversation.id,
            "title": new_conversation.title
        }

    except Exception as e:
        logger.error(f"创建对话会话失败: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"创建对话会话失败: {str(e)}"
        )


@router.get("/conversations/{user_id}")
async def get_user_conversations(
    user_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户的历史对话列表

    Args:
        user_id: 用户ID
        limit: 返回数量限制
        db: 数据库会话

    Returns:
        对话列表，包含每个对话的基本信息和最后一条消息
    """
    try:
        # 查询用户的所有对话会话(按更新时间倒序)
        result = await db.execute(
            select(SysConversation)
            .where(SysConversation.user_id == user_id)
            .order_by(desc(SysConversation.updated_at))
            .limit(limit)
        )
        conversations = result.scalars().all()

        # 为每个对话获取最后一条用户消息
        conversation_list = []
        for conv in conversations:
            # 获取该对话的最后一条用户消息
            msg_result = await db.execute(
                select(SysConversationMessage)
                .where(
                    SysConversationMessage.conversation_id == conv.id,
                    SysConversationMessage.role == MessageRoleEnum.USER
                )
                .order_by(desc(SysConversationMessage.created_at))
                .limit(1)
            )
            last_user_msg = msg_result.scalar_one_or_none()

            conversation_list.append({
                "id": conv.id,
                "title": conv.title,
                "message_count": conv.message_count,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "last_user_message": last_user_msg.content if last_user_msg else "",
                "last_message_time": last_user_msg.created_at.isoformat() if last_user_msg else conv.updated_at.isoformat()
            })

        return {
            "success": True,
            "conversations": conversation_list
        }

    except Exception as e:
        logger.error(f"获取用户对话列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取对话列表失败: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取指定对话的所有消息

    Args:
        conversation_id: 对话会话ID
        db: 数据库会话

    Returns:
        消息列表(按时间正序)
    """
    try:
        # 查询对话会话是否存在
        conv_result = await db.execute(
            select(SysConversation)
            .where(SysConversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="对话会话不存在"
            )

        # 查询该对话的所有消息(按时间正序)
        msg_result = await db.execute(
            select(SysConversationMessage)
            .where(SysConversationMessage.conversation_id == conversation_id)
            .order_by(SysConversationMessage.created_at.asc())
        )
        messages = msg_result.scalars().all()

        # 转换为响应格式
        message_list = []
        for msg in messages:
            message_data = {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "response_time": msg.response_time,
                "tokens_used": msg.tokens_used
            }

            # 如果有图表数据，解析并添加
            if msg.chart_data:
                try:
                    message_data["chart_data"] = json.loads(msg.chart_data)
                    message_data["chart_type"] = msg.chart_type
                except json.JSONDecodeError:
                    logger.warning(f"消息 {msg.id} 的图表数据解析失败")

            message_list.append(message_data)

        return {
            "success": True,
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": conversation.message_count
            },
            "messages": message_list
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话消息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取对话消息失败: {str(e)}"
        )


@router.put("/conversation/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: int,
    request: UpdateTitleRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    更新对话标题

    Args:
        conversation_id: 对话会话ID
        request: 包含新标题的请求
        db: 数据库会话

    Returns:
        成功状态
    """
    try:
        # 查询对话会话是否存在
        conv_result = await db.execute(
            select(SysConversation)
            .where(SysConversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="对话会话不存在"
            )

        # 更新标题
        conversation.title = request.title
        await db.commit()

        return {
            "success": True,
            "message": "标题已更新"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话标题失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"更新对话标题失败: {str(e)}"
        )


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    删除对话及其所有消息

    Args:
        conversation_id: 对话会话ID
        db: 数据库会话

    Returns:
        成功状态
    """
    try:
        # 查询对话会话是否存在
        conv_result = await db.execute(
            select(SysConversation)
            .where(SysConversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="对话会话不存在"
            )

        # 删除所有消息（由于外键关系，可能需要先删除消息）
        await db.execute(
            select(SysConversationMessage)
            .where(SysConversationMessage.conversation_id == conversation_id)
        )
        # 实际删除消息
        from sqlalchemy import delete as sql_delete
        await db.execute(
            sql_delete(SysConversationMessage)
            .where(SysConversationMessage.conversation_id == conversation_id)
        )

        # 删除对话
        await db.delete(conversation)
        await db.commit()

        return {
            "success": True,
            "message": "对话已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除对话失败: {str(e)}"
        )


@router.post("/conversation/generate_title")
async def generate_conversation_title(
    request: GenerateTitleRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    使用AI模型自动生成会话标题

    Args:
        request: 包含conversation_id和user_question的请求
        db: 数据库会话

    Returns:
        生成的标题
    """
    try:
        # 查询会话是否存在
        conv_result = await db.execute(
            select(SysConversation)
            .where(SysConversation.id == request.conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="对话会话不存在"
            )

        # 检查是否已经生成过标题（消息数量大于0且标题不是"新对话"）
        if conversation.message_count > 0 and conversation.title != "新对话":
            logger.info(f"会话 {request.conversation_id} 已有自定义标题，跳过生成")
            return {
                "success": True,
                "title": conversation.title,
                "updated": False
            }

        # 使用AI模型生成标题
        from services.model_cache_service import ModelCacheService
        import aiohttp

        generated_title = None
        
        try:
            model_config = await ModelCacheService.get_user_selected_model(
                user_id=conversation.user_id,
                db=db
            )

            if not model_config:
                logger.warning(f"用户 {conversation.user_id} 未找到AI配置，使用用户问题作为标题")
                # 如果没有AI配置，使用用户问题的前50个字符作为标题
                generated_title = request.user_question[:50] + ("..." if len(request.user_question) > 50 else "")
            else:
                logger.info(f"使用AI模型 {model_config.get('model_name')} 生成标题")
                
                # 调用AI生成简洁的标题
                system_prompt = (
                    "你是一个会话标题生成助手。根据用户的问题，生成一个简洁、准确的会话标题。\n"
                    "要求：\n"
                    "1. 标题长度不超过30个字符\n"
                    "2. 准确概括用户问题的核心内容\n"
                    "3. 使用中文\n"
                    "4. 不要使用引号或特殊符号\n"
                    "5. 直接返回标题文本，不要有任何其他说明\n\n"
                    f"用户问题：{request.user_question}\n\n"
                    "请生成标题："
                )

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {model_config.get('api_key', '')}",
                }

                data = {
                    "model": model_config.get('model_name', ''),
                    "messages": [{"role": "system", "content": system_prompt}],
                    "temperature": 0.7,
                    "max_tokens": 100,
                }

                # 增加重试机制
                max_retries = 2
                for attempt in range(max_retries + 1):
                    try:
                        timeout = aiohttp.ClientTimeout(total=15)  # 增加超时时间
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.post(
                                model_config.get('api_url', ''),
                                json=data,
                                headers=headers
                            ) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    # 检查响应格式
                                    if 'choices' in result and len(result['choices']) > 0:
                                        content = result['choices'][0].get('message', {}).get('content', '')
                                        if content:
                                            generated_title = content.strip()
                                            # 去除可能的引号
                                            generated_title = generated_title.strip('"').strip("'")
                                            # 限制长度（数据库限制200，但UI显示限制50）
                                            if len(generated_title) > 50:
                                                generated_title = generated_title[:50] + "..."
                                            logger.info(f"AI标题生成成功: {generated_title}")
                                            break
                                        else:
                                            logger.warning("AI返回空内容")
                                    else:
                                        logger.warning("AI返回格式异常")
                                else:
                                    logger.warning(f"AI标题生成失败: HTTP {response.status}")
                                    if attempt < max_retries:
                                        logger.info(f"重试第 {attempt + 1} 次...")
                                        await asyncio.sleep(1)  # 等待1秒后重试
                                    
                    except asyncio.TimeoutError:
                        logger.warning(f"AI标题生成超时 (尝试 {attempt + 1}/{max_retries + 1})")
                        if attempt < max_retries:
                            await asyncio.sleep(1)
                    except Exception as e:
                        logger.warning(f"AI标题生成请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                        if attempt < max_retries:
                            await asyncio.sleep(1)
                
                # 如果AI生成失败，使用备用方案
                if not generated_title:
                    logger.warning("AI标题生成完全失败，使用用户问题作为标题")
                    generated_title = request.user_question[:50] + ("..." if len(request.user_question) > 50 else "")
                    
        except Exception as e:
            logger.error(f"标题生成过程异常: {e}")
            generated_title = request.user_question[:50] + ("..." if len(request.user_question) > 50 else "")

        # 更新会话标题
        conversation.title = generated_title
        await db.commit()

        logger.info(f"会话 {request.conversation_id} 标题已自动生成: {generated_title}")

        return {
            "success": True,
            "title": generated_title,
            "updated": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成会话标题失败: {e}")
        # 如果生成失败，使用用户问题的前50个字符
        fallback_title = request.user_question[:50] + ("..." if len(request.user_question) > 50 else "")

        try:
            conv_result = await db.execute(
                select(SysConversation)
                .where(SysConversation.id == request.conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()
            if conversation:
                conversation.title = fallback_title
                await db.commit()
        except Exception as update_error:
            logger.error(f"更新fallback标题失败: {update_error}")

        return {
            "success": True,
            "title": fallback_title,
            "updated": True
        }
