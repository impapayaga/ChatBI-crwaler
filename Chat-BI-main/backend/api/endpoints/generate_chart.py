from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from api.schemas.user_input import UserInput
from api.utils.ai_utils import (
    analyze_user_intent_and_generate_sql,
    determine_chart_type,
    refine_data_with_ai,
    generate_insight_analysis,
)
from api.utils.db_utils import execute_sql_query
from api.dependencies.dependencies import get_async_session, redis_client
from services.intent_router import classify_intent, IntentType
from services.embedding_service import search_relevant_columns
from services.duckdb_query import query_parquet_with_duckdb
from services.multi_dataset_query import smart_multi_dataset_query
from services.conversation_service import (
    save_user_message,
    save_assistant_message,
    save_error_message,
    update_conversation_summary
)
from services.agents import judge_visualization_type
from api.utils.error_utils import format_error_message
from api.utils.logger import error_logger
from api.endpoints.progress_stream import get_progress_manager  # 导入进度管理器
import logging
import asyncio
import pandas as pd
import time
import math
import numpy as np
import json
import uuid  # 用于生成任务ID

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate_chart")
async def generate_chart(
    user_input: UserInput,
    background_tasks: BackgroundTasks,
    async_session: AsyncSession = Depends(get_async_session),
):
    """
    生成图表 - 支持固定Schema和用户上传数据集

    流程:
    1. 保存用户消息到数据库
    2. 意图识别(闲聊/查询/可视化)
    3. 向量检索相关列
    4. 判断查询固定表还是用户表
    5. 执行查询并返回图表数据
    6. 保存AI回复消息到数据库(包含图表数据和错误信息)
    """
    logger.info("Received user input for generating chart: %s", user_input)

    # 生成任务ID用于进度跟踪
    task_id = str(uuid.uuid4())
    progress_manager = get_progress_manager()
    
    start_time = time.time()
    conversation_id = None

    try:
        # 步骤1: 保存用户消息到数据库
        await progress_manager.update_progress(task_id, "intent", 10, "开始处理用户请求...")
        
        try:
            conversation, user_message = await save_user_message(
                async_session,
                user_input.user_input
            )
            conversation_id = conversation.id
            logger.info(f"用户消息已保存: conversation_id={conversation_id}, message_id={user_message.id}")
        except Exception as e:
            logger.warning(f"保存用户消息失败(不影响主流程): {e}")

        # 步骤2: 意图识别
        await progress_manager.update_progress(task_id, "intent", 20, "正在分析用户意图...")
        
        intent_result = await classify_intent(user_input.user_input)
        logger.info(f"意图分类: {intent_result['intent']} (置信度: {intent_result['confidence']})")

        # 如果是闲聊,直接返回文本响应
        if intent_result['intent'] == IntentType.CHITCHAT:
            await progress_manager.update_progress(task_id, "intent", 100, "识别为闲聊对话，直接回复")
            
            chitchat_message = "您好!我是ChatBI助手,可以帮您分析数据和生成图表。请上传数据文件或提出数据相关的问题。"

            # 保存AI回复到数据库
            if conversation_id:
                try:
                    response_time = int((time.time() - start_time) * 1000)
                    await save_assistant_message(
                        async_session,
                        conversation_id,
                        chitchat_message,
                        response_time=response_time
                    )

                    # 后台任务: 更新会话摘要
                    background_tasks.add_task(
                        update_summary_for_conversation,
                        conversation_id,
                        user_input.user_input,
                        chitchat_message
                    )
                except Exception as e:
                    logger.warning(f"保存AI回复失败: {e}")

            return {
                "type": "text",
                "message": chitchat_message,
                "data": [],
                "refined_data": "",
                "chart_type": "bar",
                "task_id": task_id  # 返回任务ID供前端订阅进度
            }

        # 步骤3: 数据检索
        await progress_manager.update_progress(task_id, "retrieval", 30, "正在检索相关数据...")
        
        # 步骤2: 优先使用前端传递的数据集ID，否则使用向量检索
        df = None
        data_source = "fixed_schema"  # fixed_schema, user_dataset, 或 multi_dataset
        data_source_desc = ""

        # 情况1: 前端传递了数据集ID（智慧问数模式）
        if user_input.dataset_ids and len(user_input.dataset_ids) > 0:
            logger.info(f"使用前端指定的数据集: {user_input.dataset_ids}")
            data_source = "multi_dataset" if len(user_input.dataset_ids) > 1 else "user_dataset"

            try:
                # 使用智能多数据集查询服务
                df, data_source_desc = await smart_multi_dataset_query(
                    user_input.user_input,
                    user_input.dataset_ids,
                    async_session,
                    user_id=user_input.user_id
                )

                if df is not None and not df.empty:
                    logger.info(f"智能多数据集查询成功: {len(df)} 行, {len(df.columns)} 列")
                    logger.info(f"{data_source_desc}")
                else:
                    logger.warning("智能多数据集查询返回空结果")

            except Exception as e:
                logger.error(f"智能多数据集查询失败: {e}", exc_info=True)
                df = None

        # 情况2: 前端未传递数据集ID，使用向量检索自动匹配
        else:
            logger.info("前端未指定数据集，使用向量检索自动匹配")
            relevant_columns = await search_relevant_columns(user_input.user_input, top_k=5)

            # 步骤3: 判断数据源
            if relevant_columns and relevant_columns[0]['similarity'] > 0.7:
                # 找到高相似度的用户数据集列,使用用户数据集
                dataset_id = relevant_columns[0]['dataset_id']
                data_source = "user_dataset"
                logger.info(f"向量检索匹配到数据集: {dataset_id}, 相关列: {[c['col_name'] for c in relevant_columns[:3]]}")

                # 生成针对用户数据集的SQL
                try:
                    # 构造Schema上下文
                    schema_context = "\n".join([
                        f"- {col['col_name']} ({col['col_type']}): {col.get('description', '')}"
                        for col in relevant_columns[:10]
                    ])

                    # 生成SQL查询
                    sql_query = await generate_sql_for_dataset(
                        user_input.user_input,
                        relevant_columns,
                        dataset_id
                    )

                    if sql_query:
                        # 使用DuckDB查询Parquet
                        df = await query_parquet_with_duckdb(dataset_id, sql_query)
                        logger.info(f"DuckDB查询成功: {len(df) if df is not None else 0} 行")

                except Exception as e:
                    logger.error(f"查询用户数据集失败: {e}")
                    df = None

        # 情况3: 处理查询失败的情况
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            # 如果用户明确指定了数据集，不要回退到固定Schema
            if user_input.dataset_ids and len(user_input.dataset_ids) > 0:
                logger.error("用户指定的数据集查询失败，不回退到固定Schema")
                error_msg = f"无法从您选择的数据集中查询数据。请检查：\n1. 数据集是否包含相关数据\n2. 问题描述是否准确\n3. 数据集是否已正确上传和解析"

                # 保存错误消息到数据库
                if conversation_id:
                    try:
                        await save_error_message(
                            async_session,
                            conversation_id,
                            "用户数据集查询失败",
                            user_input.user_input
                        )
                    except Exception as e:
                        logger.warning(f"保存错误消息失败: {e}")

                return {
                    "error": "用户数据集查询失败",
                    "message": error_msg,
                    "data": [],
                    "refined_data": "",
                    "chart_type": "bar",
                    "is_error": True
                }

            # 只有在用户未指定数据集且向量检索未找到时，才回退到固定Schema
            logger.info("回退到固定Schema查询")
            data_source = "fixed_schema"

            # 步骤4: SQL生成
            await progress_manager.update_progress(task_id, "sql_generation", 50, "正在生成SQL查询语句...")

            # 生成SQL查询语句(原有逻辑)
            sql_query = await analyze_user_intent_and_generate_sql(
                user_input.user_input,
                user_id=user_input.user_id
            )
            logger.info("Generated SQL query:\n %s", sql_query)

            if not sql_query:
                logger.error("Failed to generate SQL query")
                error_msg = "无法生成SQL查询语句,请检查您的输入是否正确，或者稍后再试"

                # 保存错误消息到数据库
                if conversation_id:
                    try:
                        await save_error_message(
                            async_session,
                            conversation_id,
                            "无法生成SQL查询语句",
                            user_input.user_input
                        )
                    except Exception as e:
                        logger.warning(f"保存错误消息失败: {e}")

                await progress_manager.update_progress(task_id, "sql_generation", 0, "SQL生成失败", error=True)
                return {
                    "error": "无法生成SQL查询语句",
                    "message": error_msg,
                    "data": [],
                    "refined_data": "",
                    "chart_type": "bar",
                    "is_error": True,
                    "task_id": task_id
                }

            # 步骤5: 查询执行
            await progress_manager.update_progress(task_id, "query_execution", 70, "正在执行数据查询...")

            # 执行SQL查询
            df = await execute_sql_query(sql_query, user_input, async_session)
            logger.info("Executed SQL query, resulting DataFrame:\n %s", df)

        # 检查查询结果
        if df is None or df.empty:
            logger.error("SQL query execution failed or returned empty data")
            error_msg = "SQL查询失败或返回空数据,请检查数据库连接或查询语句"

            # 保存错误消息到数据库
            if conversation_id:
                try:
                    await save_error_message(
                        async_session,
                        conversation_id,
                        "SQL查询失败或返回空数据",
                        user_input.user_input
                    )
                except Exception as e:
                    logger.warning(f"保存错误消息失败: {e}")

            await progress_manager.update_progress(task_id, "query_execution", 0, "查询执行失败", error=True)
            return {
                "error": "SQL查询失败或返回空数据",
                "message": error_msg,
                "data": [],
                "refined_data": "",
                "chart_type": "bar",
                "task_id": task_id
            }

        # 步骤6: 数据处理和可视化分析
        await progress_manager.update_progress(task_id, "query_execution", 90, "正在分析数据和生成图表...")

        # 步骤4: 使用Agent判断数据可视化类型
        viz_judgment = await judge_visualization_type(
            user_input.user_input,
            df,
            user_id=user_input.user_id
        )

        visualization_type = viz_judgment["visualization_type"]
        logger.info(f"Agent判断可视化类型: {visualization_type} (置信度: {viz_judgment['confidence']}, 理由: {viz_judgment['reason']})")

        # 步骤5: 根据可视化类型决定后续处理
        refined_data = None
        chart_type = "bar"

        if visualization_type == "chart":
            # 需要图表展示，执行数据精炼和图表类型判断
            try:
                refined_data_task = refine_data_with_ai(
                    user_input.user_input,
                    df,
                    user_id=user_input.user_id
                )
                chart_type_task = determine_chart_type(
                    user_input.user_input,
                    df.to_json(orient="records"),
                    user_id=user_input.user_id
                )

                # 等待图表生成必需的数据
                refined_data, chart_type = await asyncio.gather(
                    refined_data_task, chart_type_task, return_exceptions=True
                )

                # 验证结果
                if not refined_data or isinstance(refined_data, Exception):
                    logger.error(f"数据精炼失败: {refined_data}")
                    refined_data = None
                if not chart_type or isinstance(chart_type, Exception):
                    logger.error(f"图表类型判断失败: {chart_type}")
                    chart_type = viz_judgment.get("metadata", {}).get("suggested_chart_type", "bar")

            except Exception as e:
                logger.error(f"图表数据处理失败: {e}")
                refined_data = None
                chart_type = "bar"
        else:
            # 不需要图表，不执行数据精炼
            logger.info(f"数据类型为{visualization_type}，跳过图表数据精炼")
            refined_data = None
            chart_type = None

        # 生成洞察分析任务ID
        insight_task_id = str(uuid.uuid4())

        # 将洞察分析任务保存到Redis，供前端轮询
        try:
            task_data = {
                "user_input": user_input.user_input,
                "data": df.to_json(orient="records"),
                "user_id": user_input.user_id,
                "conversation_id": conversation_id
            }
            await redis_client.set(
                f"insight_task:{insight_task_id}",
                json.dumps(task_data),
                ex=3600  # 1小时过期
            )
            logger.info(f"洞察分析任务已保存到Redis: {insight_task_id}")
        except Exception as e:
            logger.error(f"保存洞察分析任务到Redis失败: {e}")

        # 启动洞察分析任务
        try:
            from api.endpoints.insight_task import execute_insight_analysis_task
            asyncio.create_task(
                execute_insight_analysis_task(
                    insight_task_id,
                    user_input.user_input,
                    df.to_json(orient="records"),
                    user_input.user_id
                )
            )
            logger.info(f"洞察分析任务已启动: {insight_task_id}")
        except Exception as e:
            logger.error(f"启动洞察分析任务失败: {e}")

        logger.info(f"数据处理完成: visualization_type={visualization_type}, refined_data={refined_data}, chart_type={chart_type}")

        # 将日期对象转换为字符串格式，并处理无效的float值
        data_records = df.to_dict(orient="records")
        for record in data_records:
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = value.strftime("%Y-%m-%d")
                elif isinstance(value, (float, np.float64, np.float32)):
                    # 处理无效的float值
                    if math.isnan(value) or math.isinf(value):
                        record[key] = None
                    else:
                        record[key] = float(value)
                elif isinstance(value, (np.int64, np.int32)):
                    record[key] = int(value)
                elif pd.isna(value):
                    record[key] = None

        # 步骤7: 完成处理
        await progress_manager.update_progress(task_id, "query_execution", 100, "数据处理完成")

        # 构建返回结果
        result = {
            "data": data_records,
            "refined_data": refined_data,  # chart类型时才有值
            "chart_type": chart_type,      # chart类型时才有值
            "visualization_type": visualization_type,  # 新增：展示类型
            "viz_metadata": viz_judgment.get("metadata", {}),  # Agent判断的元数据
            "data_source": data_source,
            "intent": intent_result['intent'],
            "insight_analysis": None,  # 添加洞察分析字段，初始为None
            "insight_task_id": insight_task_id,  # 返回洞察分析任务ID
            "task_id": task_id  # 返回任务ID供前端订阅进度
        }

        # 将数据存储到Redis供流式分析使用
        await redis_client.set(
            f"chart_data:{user_input.user_input}",
            df.to_json(orient="records"),
            ex=3600  # 1小时过期
        )

        logger.info("Successfully generated chart data:\n %s", result)

        # 保存AI回复到数据库(包含图表数据)
        if conversation_id:
            try:
                response_time = int((time.time() - start_time) * 1000)

                # 根据可视化类型生成合适的消息内容
                if visualization_type == "chart":
                    assistant_content = refined_data if isinstance(refined_data, str) else "已生成图表数据"
                elif visualization_type == "card":
                    assistant_content = "数据详情已准备就绪"
                elif visualization_type == "table":
                    assistant_content = f"已查询到{len(data_records)}条数据"
                else:
                    assistant_content = "数据已准备就绪"

                await save_assistant_message(
                    async_session,
                    conversation_id,
                    content=assistant_content,
                    chart_data=result,  # 保存完整的数据
                    chart_type=chart_type if chart_type else "none",
                    response_time=response_time
                    # 注意: generate_chart的token使用量难以准确统计(多个AI调用),
                    # 主要的token记录在insight_analysis_stream中完成
                )
                logger.info(f"AI回复已保存: conversation_id={conversation_id}, 可视化类型={visualization_type}")

                # 检查是否需要生成标题（新对话的第二条消息）
                from models.sys_conversation import SysConversation
                from sqlalchemy import select
                
                conv_result = await async_session.execute(
                    select(SysConversation).where(SysConversation.id == conversation_id)
                )
                conversation = conv_result.scalar_one_or_none()
                
                if conversation and conversation.message_count == 2 and conversation.title == "新对话":
                    # 后台任务: 生成会话标题
                    background_tasks.add_task(
                        generate_title_for_conversation,
                        conversation_id,
                        user_input.user_input
                    )
                    logger.info(f"已触发会话标题生成任务: conversation_id={conversation_id}")

                # 后台任务: 更新会话摘要
                background_tasks.add_task(
                    update_summary_for_conversation,
                    conversation_id,
                    user_input.user_input,
                    assistant_content
                )
            except Exception as e:
                logger.warning(f"保存AI回复失败: {e}")

        # 洞察分析任务已在上面启动，无需额外处理

        return result

    except Exception as e:
        logger.exception("An error occurred while generating chart")
        error_message = str(e)
        
        # 更新进度为错误状态
        try:
            await progress_manager.update_progress(task_id, "query_execution", 0, f"处理失败: {error_message}", error=True)
        except:
            pass  # 进度更新失败不影响主流程
        
        # 记录详细错误信息
        error_id = error_logger.log_error(
            error=e,
            context={
                "user_input": user_input.user_input,
                "conversation_id": user_input.conversation_id,
                "dataset_id": user_input.dataset_id
            },
            user_id=str(user_input.conversation_id),  # 使用conversation_id作为用户标识
            endpoint="/generate_chart"
        )
        
        # 使用错误处理工具函数分析错误类型并格式化错误信息
        error_type = "unknown_error"
        
        if "Referenced column" in error_message and "not found" in error_message:
            error_type = "column_not_found"
        elif "Connection" in error_message or "timeout" in error_message.lower():
            error_type = "connection_error"
        elif "SQL" in error_message or "query" in error_message.lower():
            error_type = "sql_error"
        elif "AI" in error_message or "model" in error_message.lower():
            error_type = "ai_model_error"
        elif "dataset" in error_message.lower():
            error_type = "dataset_error"
        elif "permission" in error_message.lower() or "access" in error_message.lower():
            error_type = "permission_error"
        
        # 格式化错误信息
        formatted_error = format_error_message(error_type, error_message, user_input.user_input)
        formatted_error["error_id"] = error_id  # 添加错误ID用于追踪

        # 保存错误消息到数据库
        if conversation_id:
            try:
                await save_error_message(
                    async_session,
                    conversation_id,
                    f"{formatted_error['message']}: {error_message}",
                    user_input.user_input
                )
            except Exception as save_err:
                logger.warning(f"保存错误消息失败: {save_err}")

        # 返回更友好的错误信息而不是抛出异常
        return {
            "error": formatted_error['message'],
            "message": error_message,
            "data": [],
            "refined_data": "",
            "chart_type": "bar",
            "is_error": True,
            "error_id": error_id,
            "task_id": task_id  # 确保错误情况下也返回task_id
        }


async def generate_sql_for_dataset(
    user_query: str,
    relevant_columns: list,
    dataset_id: str
) -> str:
    """
    为用户数据集生成SQL查询

    使用LLM生成更智能的SQL查询
    """
    from api.utils.ai_utils import call_configured_ai_model

    # 构建列信息描述
    col_descriptions = []
    for col in relevant_columns[:15]:  # 使用前15个相关列
        col_type = col.get('col_type', 'unknown')
        col_name = col['col_name']
        samples = col.get('sample_values', [])
        sample_str = ', '.join([str(s) for s in samples[:3]]) if samples else ''

        col_desc = f"- `{col_name}` ({col_type})"
        if sample_str:
            col_desc += f" - 示例: {sample_str}"
        col_descriptions.append(col_desc)

    schema_context = '\n'.join(col_descriptions)

    system_prompt = f"""你是一个专业的SQL查询生成助手。根据用户问题和数据集schema生成DuckDB SQL查询。

**重要规则:**
1. 表名必须使用 `dataset` (不要使用table_name等占位符)
2. 列名必须用双引号包裹，如 "column_name"
3. 只能使用提供的列名，不要编造列名
4. 查询结果限制在100行以内
5. 使用标准SQL语法
6. 不要使用注释
7. 只生成一条SQL语句

**数据集Schema:**
{schema_context}

**用户问题:** {user_query}

请生成SQL查询，使用以下格式返回:
```sql
SELECT ...
```

注意:
- 如果问题涉及行数统计，使用 COUNT(*)
- 如果问题涉及数据内容，使用 SELECT * 或选择相关列
- 如果需要聚合，使用合适的GROUP BY
- 优先使用相关度高的列
"""

    try:
        ai_response = await call_configured_ai_model(system_prompt, user_query, user_id=1)

        if ai_response:
            # 提取SQL
            sql_start = ai_response.find("```sql\n")
            if sql_start != -1:
                sql_start += len("```sql\n")
                sql_end = ai_response.find("\n```", sql_start)
                if sql_end != -1:
                    sql_query = ai_response[sql_start:sql_end].strip()

                    # 验证SQL不包含占位符
                    if 'table_name' in sql_query.lower() or 'column_name' in sql_query.lower():
                        logger.warning(f"生成的SQL包含占位符，使用回退方案")
                        return generate_fallback_sql(user_query, relevant_columns)

                    logger.info(f"LLM生成的SQL: {sql_query}")
                    return sql_query

            # 如果没有找到SQL代码块，尝试直接提取
            lines = ai_response.strip().split('\n')
            for line in lines:
                if line.strip().upper().startswith('SELECT'):
                    return line.strip()

        logger.warning("LLM未能生成有效SQL，使用回退方案")
        return generate_fallback_sql(user_query, relevant_columns)

    except Exception as e:
        logger.error(f"LLM生成SQL失败: {e}，使用回退方案")
        return generate_fallback_sql(user_query, relevant_columns)


def generate_fallback_sql(user_query: str, relevant_columns: list) -> str:
    """
    回退SQL生成方案：基于规则的SQL生成
    """
    # 提取列名
    col_names = [col['col_name'] for col in relevant_columns[:10]]

    # 检测是否需要聚合或统计
    agg_keywords = ['多少行', '行数', '总共', '数量', 'count', '总计', '总和', 'sum', '平均', 'avg']
    need_count = any(kw in user_query.lower() for kw in agg_keywords)

    if need_count or '多少' in user_query:
        # 统计查询
        return "SELECT COUNT(*) as row_count FROM dataset"

    # 内容查询 - 检测是否需要聚合
    agg_keywords2 = ['统计', '分组', 'group', '按照']
    need_agg = any(kw in user_query.lower() for kw in agg_keywords2)

    if need_agg:
        # 尝试找到数值列和分组列
        numeric_cols = [c['col_name'] for c in relevant_columns if c.get('col_type') in ['int64', 'float64', 'int', 'float', 'number']]
        cat_cols = [c['col_name'] for c in relevant_columns if c.get('col_type') in ['string', 'object', 'category', 'date']]

        if numeric_cols and cat_cols:
            return f'SELECT "{cat_cols[0]}", SUM("{numeric_cols[0]}") as total FROM dataset GROUP BY "{cat_cols[0]}" ORDER BY total DESC LIMIT 100'

    # 检测排序需求
    order_by = ""
    if "最新" in user_query or "最近" in user_query:
        date_cols = [c['col_name'] for c in relevant_columns if 'date' in c['col_name'].lower() or 'time' in c['col_name'].lower()]
        if date_cols:
            order_by = f' ORDER BY "{date_cols[0]}" DESC'
    elif "最早" in user_query:
        date_cols = [c['col_name'] for c in relevant_columns if 'date' in c['col_name'].lower() or 'time' in c['col_name'].lower()]
        if date_cols:
            order_by = f' ORDER BY "{date_cols[0]}" ASC'
    elif "最高" in user_query or "最大" in user_query:
        numeric_cols = [c['col_name'] for c in relevant_columns if c.get('col_type') in ['int64', 'float64', 'int', 'float', 'number']]
        if numeric_cols:
            order_by = f' ORDER BY "{numeric_cols[0]}" DESC'
    elif "最低" in user_query or "最小" in user_query:
        numeric_cols = [c['col_name'] for c in relevant_columns if c.get('col_type') in ['int64', 'float64', 'int', 'float', 'number']]
        if numeric_cols:
            order_by = f' ORDER BY "{numeric_cols[0]}" ASC'

    # 简单查询 - 显示前几行数据
    if col_names:
        cols_str = ', '.join([f'"{col}"' for col in col_names[:10]])
        sql = f"SELECT {cols_str} FROM dataset"
    else:
        sql = "SELECT * FROM dataset"
    
    # 添加限制
    if "前" in user_query and any(char.isdigit() for char in user_query):
        import re
        numbers = re.findall(r'\d+', user_query)
        if numbers:
            limit = numbers[0]
            sql += f"{order_by} LIMIT {limit}"
        else:
            sql += f"{order_by} LIMIT 10"
    else:
        sql += f"{order_by} LIMIT 10"
    
    return sql


async def store_insight_analysis(user_input, insight_task):
    """存储已经开始的洞察分析任务结果"""
    try:
        insight_analysis = await insight_task
        if insight_analysis:
            logger.info("Generated insight analysis: %s", insight_analysis)
            # 将洞察分析结果存储到 Redis 中，设置过期时间
            await redis_client.set(f"insight_analysis:{user_input}", insight_analysis, ex=3600)  # 1小时过期
        else:
            logger.error("Failed to generate insight analysis")
    except Exception as e:
        logger.error(f"Error storing insight analysis: {e}")


async def store_insight_analysis_with_task_id(user_input, insight_task, task_id):
    """存储带任务ID的洞察分析任务结果"""
    import json
    try:
        # 更新任务状态为运行中
        task_data = {
            "task_id": task_id,
            "status": "running",
            "progress": 50,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        await redis_client.set(f"insight_task:{task_id}", json.dumps(task_data, ensure_ascii=False), ex=86400)
        
        # 等待洞察分析完成
        insight_analysis = await insight_task
        
        if insight_analysis:
            logger.info(f"Generated insight analysis for task {task_id}: %s", insight_analysis)
            
            # 更新任务状态为完成
            task_data.update({
                "status": "completed",
                "progress": 100,
                "result": insight_analysis,
                "completed_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            await redis_client.set(f"insight_task:{task_id}", json.dumps(task_data, ensure_ascii=False), ex=86400)
            
            # 同时保持原有的存储方式以兼容现有功能
            await redis_client.set(f"insight_analysis:{user_input}", insight_analysis, ex=3600)
        else:
            logger.error(f"Failed to generate insight analysis for task {task_id}")
            # 更新任务状态为失败
            task_data.update({
                "status": "failed",
                "progress": 100,
                "error": "生成洞察分析失败",
                "updated_at": datetime.now().isoformat()
            })
            await redis_client.set(f"insight_task:{task_id}", json.dumps(task_data, ensure_ascii=False), ex=86400)
            
    except Exception as e:
        logger.error(f"Error storing insight analysis for task {task_id}: {e}")
        # 更新任务状态为失败
        task_data = {
            "task_id": task_id,
            "status": "failed",
            "progress": 100,
            "error": f"执行洞察分析出错: {str(e)}",
            "updated_at": datetime.now().isoformat()
        }
        await redis_client.set(f"insight_task:{task_id}", json.dumps(task_data, ensure_ascii=False), ex=86400)


async def generate_title_for_conversation(conversation_id: int, user_question: str):
    """
    后台任务: 生成会话标题

    Args:
        conversation_id: 对话会话ID
        user_question: 用户问题
    """
    try:
        from services.model_cache_service import ModelCacheService
        from models.sys_conversation import SysConversation
        from db.session import async_session
        from sqlalchemy import select
        import aiohttp

        async with async_session() as db:
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
        logger.error(f"生成会话标题失败: {e}")


async def update_summary_for_conversation(conversation_id: int, user_question: str, assistant_response: str):
    """
    后台任务: 更新会话摘要

    Args:
        conversation_id: 对话会话ID
        user_question: 用户问题
        assistant_response: AI回复
    """
    try:
        from services.model_cache_service import ModelCacheService
        from models.sys_conversation import SysConversation
        from db.session import async_session
        from sqlalchemy import select

        async with async_session() as db:
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
            logger.info(f"会话摘要已更新: conversation_id={conversation_id}")

    except Exception as e:
        logger.error(f"后台更新会话摘要失败: {e}")




