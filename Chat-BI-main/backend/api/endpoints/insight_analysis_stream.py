from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import logging
import asyncio
import aiohttp
import time

from models.sys_ai_model_config import SysAiModelConfig
from db.session import async_session
from services.conversation_service import save_user_message, save_assistant_message, update_conversation_summary

router = APIRouter()
logger = logging.getLogger(__name__)


async def generate_title_async(conversation_id: int, user_question: str):
    """异步生成会话标题"""
    try:
        async with async_session() as db:
            from services.model_cache_service import ModelCacheService
            from models.sys_conversation import SysConversation

            # 获取会话信息
            conv_result = await db.execute(
                select(SysConversation).where(SysConversation.id == conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                logger.warning(f"会话 {conversation_id} 不存在，无法生成标题")
                return

            # 再次检查是否需要生成标题
            if conversation.title != "新对话":
                logger.info(f"会话 {conversation_id} 已有标题，跳过生成")
                return

            generated_title = None
            
            try:
                # 获取AI配置
                model_config = await ModelCacheService.get_user_selected_model(
                    user_id=conversation.user_id,
                    db=db
                )

                if not model_config:
                    logger.warning(f"用户 {conversation.user_id} 没有AI配置，使用用户问题的前50个字符作为标题")
                    # 没有AI配置，使用用户问题的前50个字符作为标题
                    generated_title = user_question[:50] + ("..." if len(user_question) > 50 else "")
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
                        f"用户问题：{user_question}\n\n"
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
                        generated_title = user_question[:50] + ("..." if len(user_question) > 50 else "")
                        
            except Exception as e:
                logger.error(f"标题生成过程异常: {e}")
                generated_title = user_question[:50] + ("..." if len(user_question) > 50 else "")

            # 更新会话标题
            if generated_title:
                conversation.title = generated_title
                await db.commit()
                logger.info(f"会话 {conversation_id} 标题已自动生成: {generated_title}")
            else:
                logger.error(f"会话 {conversation_id} 标题生成失败，保持原标题")

    except Exception as e:
        logger.error(f"异步生成会话标题失败: {e}")


async def update_summary_async(conversation_id: int, user_question: str, assistant_response: str):
    """异步更新会话摘要"""
    try:
        async with async_session() as db:
            from services.model_cache_service import ModelCacheService
            from models.sys_conversation import SysConversation

            # 获取会话信息
            conv_result = await db.execute(
                select(SysConversation).where(SysConversation.id == conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                logger.warning(f"会话 {conversation_id} 不存在，无法更新摘要")
                return

            # 获取AI配置
            model_config = await ModelCacheService.get_user_selected_model(
                user_id=conversation.user_id,
                db=db
            )

            # 更新摘要
            await update_conversation_summary(
                db,
                conversation_id,
                user_question,
                assistant_response,
                model_config=model_config
            )

    except Exception as e:
        logger.error(f"异步更新会话摘要失败: {e}")


async def get_db():
    async with async_session() as session:
        yield session


async def get_default_ai_config_for_user(user_id: int, db: AsyncSession):
    """获取用户的默认AI配置"""
    result = await db.execute(
        select(SysAiModelConfig)
        .where(
            SysAiModelConfig.user_id == user_id,
            SysAiModelConfig.is_default == True,
            SysAiModelConfig.is_active == True
        )
    )
    return result.scalar_one_or_none()


class StreamInsightRequest(BaseModel):
    user_input: str
    data: str  # JSON格式的数据


@router.post("/insight_analysis_stream")
async def insight_analysis_stream(request: StreamInsightRequest):
    """流式洞察分析"""

    # 用于收集完整的流式输出
    complete_content = []
    conversation_id = None
    start_time = time.time()
    tokens_used = None  # 记录token使用量
    prompt_tokens = 0  # 提示词token数
    completion_tokens = 0  # 生成token数

    async def generate_stream():
        nonlocal complete_content, conversation_id, start_time, tokens_used, prompt_tokens, completion_tokens

        try:
            # 获取AI配置 (使用Redis缓存)
            from services.model_cache_service import ModelCacheService

            # 先解析data字段,判断是否为普通聊天模式（必须在数据库会话之前）
            # 初始化变量，避免在except块外使用未定义的变量
            is_chat_mode = False
            is_analysis_mode = False
            data_obj = {}
            
            try:
                data_obj = json.loads(request.data)
                is_chat_mode = data_obj.get('mode') == 'chat'
                is_analysis_mode = data_obj.get('mode') == 'analysis'
                logger.info(f"解析请求数据: mode={data_obj.get('mode')}, conversation_id={data_obj.get('conversation_id')}, is_chat_mode={is_chat_mode}, is_analysis_mode={is_analysis_mode}")
            except Exception as e:
                logger.error(f"解析请求数据失败: {e}")
                is_chat_mode = False
                is_analysis_mode = False

            async with async_session() as db:
                # 只在聊天模式下保存用户消息，洞察分析模式不保存用户消息
                if is_chat_mode:
                    try:
                        # 优先使用传递的conversation_id，如果没有则创建新对话
                        conversation_id = data_obj.get('conversation_id')
                        if conversation_id and conversation_id != 'null' and conversation_id != 'undefined':
                            # 使用现有对话，直接保存用户消息
                            from services.conversation_service import save_message
                            from models.sys_conversation import MessageRoleEnum
                            user_message = await save_message(
                                db,
                                conversation_id,
                                MessageRoleEnum.USER,
                                request.user_input
                            )
                            logger.info(f"用户消息已保存到现有对话: conversation_id={conversation_id}, message_id={user_message.id}")
                        else:
                            # 创建新对话
                            conversation, user_message = await save_user_message(
                                db,
                                request.user_input,
                                user_id=1
                            )
                            conversation_id = conversation.id
                            logger.info(f"用户消息已保存到新对话: conversation_id={conversation_id}, message_id={user_message.id}")
                    except Exception as e:
                        logger.warning(f"保存用户消息失败(不影响主流程): {e}")
                elif is_analysis_mode:
                    # 洞察分析模式：从data中获取conversation_id，不保存用户消息
                    try:
                        conversation_id = data_obj.get('conversation_id')
                        if not conversation_id:
                            logger.warning("洞察分析模式缺少conversation_id，无法保存AI回复")
                    except Exception as e:
                        logger.warning(f"获取conversation_id失败: {e}")
                else:
                    # 默认模式：保存用户消息（向后兼容）
                    try:
                        conversation, user_message = await save_user_message(
                            db,
                            request.user_input,
                            user_id=1
                        )
                        conversation_id = conversation.id
                        logger.info(f"用户消息已保存(默认模式): conversation_id={conversation_id}, message_id={user_message.id}")
                    except Exception as e:
                        logger.warning(f"保存用户消息失败(不影响主流程): {e}")

                model_config = await ModelCacheService.get_user_selected_model(
                    user_id=1,  # 暂时使用固定用户ID
                    db=db
                )

                if not model_config:
                    yield f"data: {json.dumps({'error': '未找到AI配置，请先在设置中配置AI模型'}, ensure_ascii=False)}\n\n"
                    return

                # 转换为API调用格式
                config = {
                    'apiKey': model_config.get('api_key', ''),
                    'baseUrl': model_config.get('api_url', ''),
                    'model': model_config.get('model_name', ''),
                    'temperature': model_config.get('temperature', 0.7),
                    'maxTokens': model_config.get('max_tokens', 2000)
                }

                # 如果是聊天模式，进行意图识别（仅用于日志记录，不影响处理流程），并构建上下文
                chat_messages = []
                if is_chat_mode:
                    from services.intent_router import classify_intent, IntentType
                    from sqlalchemy import select
                    from models.sys_conversation import SysConversation, SysConversationMessage
                    
                    try:
                        intent_result = await classify_intent(request.user_input)
                        logger.info(f"聊天模式意图识别: {intent_result['intent']} (置信度: {intent_result['confidence']})")
                        # 注意：即使是闲聊，也继续走AI对话流程，让AI模型生成动态回复
                    except Exception as e:
                        logger.warning(f"意图识别失败，继续正常处理: {e}")

                    # 构建近期对话窗口 + 会话摘要
                    try:
                        if conversation_id:
                            # 读取会话摘要
                            conv_result = await db.execute(
                                select(SysConversation).where(SysConversation.id == conversation_id)
                            )
                            conv = conv_result.scalar_one_or_none()
                            summary_text = (conv.summary or '').strip() if conv else ''

                            # 读取最近N条消息（不包含当前轮）
                            msg_result = await db.execute(
                                select(SysConversationMessage)
                                .where(SysConversationMessage.conversation_id == conversation_id)
                                .order_by(SysConversationMessage.created_at.desc())
                                .limit(8)
                            )
                            recent_msgs = list(reversed(msg_result.scalars().all()))

                            # 将摘要作为system前置（如有）
                            if summary_text:
                                chat_messages.append({
                                    'role': 'system',
                                    'content': f"会话摘要：{summary_text}"
                                })

                            # 注入最近消息（仅保留文本内容；如含图表，附上简要说明）
                            for m in recent_msgs:
                                role = 'user' if m.role.value.lower() == 'user' else 'assistant'
                                content = m.content or ''
                                # 如果是图表消息，补充一行上下文摘要
                                if (not content) and m.chart_data:
                                    try:
                                        import json as _json
                                        _cd = _json.loads(m.chart_data)
                                        cols = []
                                        if isinstance(_cd, dict) and 'data' in _cd and isinstance(_cd['data'], list) and _cd['data']:
                                            cols = list(_cd['data'][0].keys())[:6]
                                        content = f"[上轮图表上下文] 列: {', '.join(cols)}"
                                    except Exception:
                                        content = "[上轮图表上下文]"
                                if content:
                                    chat_messages.append({'role': role, 'content': content})

                    except Exception as e:
                        logger.warning(f"构建对话上下文失败: {e}")

            # 动态获取当前时间信息
            from datetime import datetime
            import pytz

            # 获取中国时区的当前时间
            china_tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(china_tz)
            current_date = current_time.strftime('%Y-%m-%d')
            current_year = current_time.year
            current_month = current_time.month

            # 根据模式构建不同的提示词/消息
            if is_chat_mode:
                # 普通聊天模式：采用混合方案（近期窗口 + 摘要 + 本轮问题）
                system_prompt = (
                    "你是ChatBI助手，一个专业的商业智能助手。\n\n"
                    f"当前时间：{current_date}\n\n"
                    "你的职责：\n"
                    "1. 友好、专业地回答用户的各种问题，包括闲聊、数据分析咨询等\n"
                    "2. 如果用户询问数据分析相关问题，引导他们上传数据集或选择已有数据集\n"
                    "3. 如果用户询问与数据分析无关的问题（如天气、日常聊天等），自然友好地回答\n"
                    "4. 简洁明了地表达，使用Markdown格式\n\n"
                    "回答需基于下方对话上下文（若有）与当前问题。"
                )
                # 组装消息：system + 上文窗口 + 当前问题
                messages_payload = [{'role': 'system', 'content': system_prompt}]
                if chat_messages:
                    messages_payload.extend(chat_messages)
                # 当前问题作为最后一条用户消息
                messages_payload.append({'role': 'user', 'content': request.user_input})
            else:
                # 数据洞察分析模式
                system_prompt = (
                    "基于用户的问题和查询结果，生成深入的洞察分析。分析应该简洁明了，并提供从数据中得出的有意义的见解。\n\n"
                    f"当前时间上下文：今天是{current_date}，当前年份是{current_year}年{current_month}月\n"
                    f"数据时间范围：2024年6月至12月\n\n"
                    f"用户问题：{request.user_input}\n\n"
                    f"查询结果：\n{request.data}\n\n"
                    "请按照以下Markdown格式返回分析结果：\n\n"
                    "## 📊 数据洞察分析\n\n"
                    "### 🔍 关键发现\n"
                    "- **核心指标**：[描述主要数据指标]\n"
                    "- **数据趋势**：[描述数据变化趋势]\n"
                    "- **对比分析**：[如有对比数据，进行分析]\n\n"
                    "### 💡 深度解读\n"
                    "[详细分析数据背后的原因和意义]\n\n"
                    "### 📈 业务启示\n"
                    "1. **短期影响**：[分析对当前的影响]\n"
                    "2. **长期趋势**：[预测未来可能的发展]\n"
                    "3. **行动建议**：[基于数据提供的建议]\n\n"
                    "### 🎯 关注要点\n"
                    "> [重点提醒或需要特别关注的数据点]\n\n"
                    "> 如果没有获取图表数据不做分析，直接告诉客户缺少数据，不要做任何分析\n\n"
                    "请确保分析内容准确、有见地，并与用户的问题紧密相关。使用中文回答。直接返回Markdown格式的分析内容，不要使用代码块包裹。"
                )

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['apiKey']}",
            }

            # 适配：聊天模式使用messages_payload；洞察模式仍使用单system
            if is_chat_mode:
                data = {
                    "model": config["model"],
                    "messages": messages_payload,
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("maxTokens", 2000),
                    "stream": True,
                }
            else:
                data = {
                    "model": config["model"],
                    "messages": [{"role": "system", "content": system_prompt}],
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("maxTokens", 2000),
                    "stream": True,
                }

            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    config["baseUrl"], json=data, headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        yield f"data: {json.dumps({'error': f'AI调用失败: {error_text}'})}\n\n"
                        return

                    # 处理流式响应
                    async for line in response.content:
                        if line:
                            line_text = line.decode("utf-8").strip()
                            if line_text.startswith("data: "):
                                data_part = line_text[6:]  # 去掉'data: '前缀

                                if data_part == "[DONE]":
                                    yield f"data: {json.dumps({'done': True})}\n\n"
                                    break

                                try:
                                    chunk_data = json.loads(data_part)
                                    if (
                                        "choices" in chunk_data
                                        and len(chunk_data["choices"]) > 0
                                    ):
                                        choice = chunk_data["choices"][0]
                                        if (
                                            "delta" in choice
                                            and "content" in choice["delta"]
                                        ):
                                            content = choice["delta"]["content"]
                                            if content:
                                                # 收集完整内容
                                                complete_content.append(content)
                                                yield f"data: {json.dumps({'content': content})}\n\n"

                                    # 提取token使用量（支持多种API响应格式）
                                    if "usage" in chunk_data:
                                        usage_data = chunk_data["usage"]
                                        # 优先记录详细的token统计
                                        prompt_tokens = usage_data.get("prompt_tokens", 0)
                                        completion_tokens = usage_data.get("completion_tokens", 0)
                                        tokens_used = usage_data.get("total_tokens") or (prompt_tokens + completion_tokens)
                                        logger.info(f"收到token使用量: 提示={prompt_tokens}, 生成={completion_tokens}, 总计={tokens_used}")
                                except json.JSONDecodeError:
                                    continue
                                except Exception as e:
                                    logger.error(f"处理流式数据出错: {e}")
                                    continue

            # 流式输出完成后,保存到数据库
            if conversation_id and complete_content:
                try:
                    async with async_session() as db:
                        full_content = ''.join(complete_content)
                        response_time = int((time.time() - start_time) * 1000)
                        await save_assistant_message(
                            db,
                            conversation_id,
                            content=full_content,
                            response_time=response_time,
                            tokens_used=tokens_used
                        )
                        logger.info(f"AI流式回复已保存: conversation_id={conversation_id}, 内容长度={len(full_content)}, tokens使用量={tokens_used}")

                        # 检查是否需要生成会话标题（仅第一轮对话：1条用户消息+1条AI消息=2条）
                        from models.sys_conversation import SysConversation
                        conv_result = await db.execute(
                            select(SysConversation).where(SysConversation.id == conversation_id)
                        )
                        conversation = conv_result.scalar_one_or_none()

                        if conversation and conversation.message_count == 2 and conversation.title == "新对话":
                            # 异步生成标题（不阻塞流式输出）
                            asyncio.create_task(generate_title_async(conversation_id, request.user_input))
                            logger.info(f"已触发会话标题生成任务: conversation_id={conversation_id}")

                        # 异步更新会话摘要（每轮对话都更新）
                        asyncio.create_task(update_summary_async(conversation_id, request.user_input, full_content))
                        logger.info(f"已触发会话摘要更新任务: conversation_id={conversation_id}")

                except Exception as e:
                    logger.error(f"保存AI流式回复失败: {e}")

        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'error': '请求超时'})}\n\n"
        except Exception as e:
            logger.error(f"流式洞察分析出错: {e}")
            yield f"data: {json.dumps({'error': f'分析失败: {str(e)}'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/insight_analysis_stream/{user_input}")
async def insight_analysis_stream_get(user_input: str):
    """通过GET方式获取流式洞察分析"""

    async def generate_stream():
        try:
            # 从Redis获取相关数据
            from api.dependencies.dependencies import redis_client

            data_key = f"chart_data:{user_input}"
            data_json = await redis_client.get(data_key)

            if not data_json:
                yield f"data: {json.dumps({'error': '未找到相关数据'})}\n\n"
                return

            # 创建请求对象
            request = StreamInsightRequest(user_input=user_input, data=data_json)

            # 调用流式分析
            async for chunk in insight_analysis_stream(request).body_iterator:
                yield chunk

        except Exception as e:
            logger.error(f"GET流式洞察分析出错: {e}")
            yield f"data: {json.dumps({'error': f'分析失败: {str(e)}'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )
