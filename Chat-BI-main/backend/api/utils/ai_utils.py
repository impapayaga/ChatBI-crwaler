import os
import json
import logging
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv
import asyncio  # 添加 asyncio 模块
import aiohttp

# 加载环境变量
load_dotenv()

# 从环境变量中获取API URL
api_url_14b_chat = os.getenv("API_URL_14B_CHAT")
api_url_14b_generate = os.getenv("API_URL_14B_GENERATE")
api_url_72b_chat = os.getenv("API_URL_72B_CHAT")

# 初始化session对象并配置重试机制
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

# 使用模型选择
# 定义模型类型变量
model_type = "72B-chat"  # 可以是 "14B-chat", "14B-generate", "72B-chat"

# 定义模型配置映射
model_config = {
    "14B-chat": {
        "api_url": api_url_14b_chat,
        "model": "qwen2.5:14b",
        "call_function": "call_qwen_chat_14B_api",
    },
    "14B-generate": {
        "api_url": api_url_14b_generate,
        "model": "qwen2.5:14b",
        "call_function": "call_qwen_generate_14B_api",
    },
    "72B-chat": {
        "api_url": api_url_72b_chat,
        "model": "/root/.cache/modelscope",
        "call_function": "call_qwen_chat_72B_api",
    },
}


def make_api_request(api_url, headers, data):
    try:
        # 增加超时时间到180秒
        response = session.post(
            api_url, headers=headers, data=json.dumps(data), timeout=180
        )
        response.raise_for_status()
        if response.text.strip():
            return response.json()
        else:
            logging.error("API响应为空")
            return None
    except requests.exceptions.ConnectionError as e:
        logging.error(f"连接错误: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logging.error(f"请求超时: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误: {e}")
        return None
    except Exception as e:
        logging.error(f"未知错误: {e}")
        return None


def call_qwen_chat_14B_api(api_url, model, system_prompt, user_input):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.5,
        "top_p": 1,
        "repetition_penalty": 1.05,
        "max_tokens": 4000,
        "stream": False,
    }
    result = make_api_request(api_url, headers, data)
    if result and "message" in result and "content" in result["message"]:
        return result["message"]["content"]
    else:
        logging.error("API响应中没有预期的'message'或'content'字段")
        return None


def call_qwen_generate_14B_api(api_url, model, system_prompt):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": system_prompt,
        "stream": False,
    }
    result = make_api_request(api_url, headers, data)
    if result and "response" in result:
        return result["response"]
    else:
        logging.error("API响应中没有预期的'response'字段")
        return None


def call_qwen_chat_72B_api(api_url, model, system_prompt, user_input=None):
    headers = {"Content-Type": "application/json"}
    messages = [{"role": "system", "content": system_prompt}]
    if user_input:
        messages.append({"role": "user", "content": user_input})

    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "top_p": 1,
        "repetition_penalty": 1.05,
        "stream": False,
    }
    result = make_api_request(api_url, headers, data)
    if result and "choices" in result and len(result["choices"]) > 0:
        message = result["choices"][0]["message"]
        if "content" in message:
            return message["content"]
        else:
            logging.error("API响应中没有预期的'content'字段")
            return None
    else:
        logging.error("API响应中没有预期的'choices'字段或'choices'为空")
        return None


def call_qwen_model(model_type, system_prompt, user_input=None):
    config = model_config.get(model_type)
    if not config:
        logging.error("未知的模型类型")
        return None

    api_url = config["api_url"]
    model = config["model"]
    call_function = config["call_function"]

    if call_function == "call_qwen_chat_14B_api":
        return call_qwen_chat_14B_api(api_url, model, system_prompt, user_input)
    elif call_function == "call_qwen_generate_14B_api":
        return call_qwen_generate_14B_api(api_url, model, system_prompt)
    elif call_function == "call_qwen_chat_72B_api":
        return call_qwen_chat_72B_api(api_url, model, system_prompt, user_input)
    else:
        logging.error("未知的调用函数")
        return None


async def get_configured_ai_model(user_id: int = 1):
    """
    获取配置的AI模型

    优先从Redis获取用户选择的模型配置
    如果Redis中没有,则从数据库获取默认配置

    Args:
        user_id: 用户ID,默认为1

    Returns:
        模型配置字典,包含apiKey, baseUrl, model等信息
    """
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from services.model_cache_service import ModelCacheService
        from db.session import async_session

        async with async_session() as db:
            # 从Redis/数据库获取用户选择的模型配置
            model_config = await ModelCacheService.get_user_selected_model(
                user_id=user_id,
                db=db
            )

            if model_config:
                return {
                    'apiKey': model_config.get('api_key', ''),
                    'baseUrl': model_config.get('api_url', ''),
                    'model': model_config.get('model_name', ''),
                    'temperature': model_config.get('temperature', 0.7),
                    'maxTokens': model_config.get('max_tokens', 2000)
                }

            logging.warning(f"用户{user_id}没有可用的AI模型配置")
            return None
    except Exception as e:
        logging.error(f"获取AI配置失败: {e}")
        return None

async def call_configured_ai_model(system_prompt, user_input=None, user_id: int = 1, return_usage: bool = False):
    """
    调用配置的AI模型

    Args:
        system_prompt: 系统提示词
        user_input: 用户输入(可选)
        user_id: 用户ID,用于获取用户选择的模型配置
        return_usage: 是否返回token使用量信息

    Returns:
        如果return_usage=False: AI模型的响应内容
        如果return_usage=True: (响应内容, token使用量字典)
    """
    config = await get_configured_ai_model(user_id=user_id)

    if config:
        # 使用配置的模型
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['apiKey']}"
            }

            messages = [{"role": "system", "content": system_prompt}]
            if user_input:
                messages.append({"role": "user", "content": user_input})

            data = {
                "model": config['model'],
                "messages": messages,
                "temperature": config.get('temperature', 0.7),
                "max_tokens": config.get('maxTokens', 2000)
            }

            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(config['baseUrl'], json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']

                            # 提取token使用量
                            if return_usage:
                                usage = result.get('usage', {})
                                token_info = {
                                    'prompt_tokens': usage.get('prompt_tokens', 0),
                                    'completion_tokens': usage.get('completion_tokens', 0),
                                    'total_tokens': usage.get('total_tokens', 0)
                                }
                                return content, token_info
                            else:
                                return content
                    else:
                        error_text = await response.text()
                        logging.error(f"配置的AI调用失败: HTTP {response.status}: {error_text}")

        except Exception as e:
            logging.error(f"调用配置的AI模型失败: {e}")

    # 如果配置模型失败，回退到原有模型
    logging.info("回退到原有AI模型")
    content = call_qwen_model(model_type, system_prompt, user_input)

    if return_usage:
        # 回退模型无法获取token使用量
        return content, {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    else:
        return content

async def analyze_user_intent_and_generate_sql(user_input, retry_count=3, user_id: int = 1):
    """
    分析用户意图并生成SQL查询

    Args:
        user_input: 用户输入
        retry_count: 重试次数
        user_id: 用户ID,用于获取用户选择的模型配置

    Returns:
        生成的SQL查询语句
    """
    # 动态获取当前时间信息
    from datetime import datetime
    import pytz

    # 获取中国时区的当前时间
    china_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(china_tz)
    current_year = current_time.year
    current_month = current_time.month
    current_date = current_time.strftime('%Y-%m-%d')

    # 从环境变量获取数据库表结构
    database_schema = os.getenv("DATABASE_SCHEMA", "")

    system_prompt = (
        "Analyze the user input and generate the corresponding SQL query based on the existing database table clause. "
        f"CURRENT TIME CONTEXT: Today is {current_date}, current year is {current_year}, current month is {current_month}. "
        "IMPORTANT: The data in the database spans from June 2024 to December 2024. "
        "When users mention months without specifying year (like '8月', '9月', 'August', 'September'), "
        f"intelligently determine the year based on context - if they're asking about recent months and it's {current_year}, "
        f"they likely mean {current_year} if the month has data, otherwise assume 2024. "
        "Always consider data availability when choosing the year. "
        f"My database build statement:\n\n{database_schema}\n"
        "The SQL query must be formatted in Markdown as follows:\n\n"
        "```sql\n"
        "SELECT * FROM table_name;\n"
        "```\n\n"
        f"TIME INTELLIGENCE RULES:\n"
        f"1. Current date: {current_date}\n"
        f"2. Available data range: June 2024 - December 2024\n"
        f"3. When user asks about months without year, choose the most logical year based on data availability\n"
        f"4. For historical analysis, prefer 2024 data when available\n"
        f"5. Always validate that your chosen date range has data in the database"
    )

    for attempt in range(retry_count):
        try:
            ai_response = await call_configured_ai_model(system_prompt, user_input, user_id=user_id)

            if ai_response:
                sql_start = ai_response.find("```sql\n") + len("```sql\n")
                sql_end = ai_response.find("\n```", sql_start)
                sql_query = ai_response[sql_start:sql_end].strip()

                if sql_query:
                    return sql_query
                else:
                    logging.warning(
                        f"第 {attempt + 1} 次尝试未能从AI的回复中提取SQL语句"
                    )
            else:
                logging.warning(f"第 {attempt + 1} 次尝试AI未能生成有效的回复")
        except Exception as e:
            logging.error(f"第 {attempt + 1} 次尝试发生错误: {e}")

    # 如果所有尝试都失败，返回一个默认的SQL查询
    logging.error("多次尝试后仍未能生成SQL语句，返回默认查询")
    if "销售" in user_input or "sales" in user_input.lower():
        return "SELECT sale_date, product_name, amount, quantity FROM sales ORDER BY sale_date DESC LIMIT 10"
    elif "车流" in user_input or "人流量" in user_input:
        return "SELECT statistics_date, all_count, in_count, out_count FROM pl_mobile_people_flow_data ORDER BY statistics_date DESC LIMIT 10"
    elif "人口" in user_input:
        return "SELECT date_time, num FROM pl_pop_trend_of_end_year ORDER BY date_time DESC LIMIT 10"
    else:
        # 默认返回sales表数据
        return "SELECT sale_date, product_name, amount, quantity FROM sales ORDER BY sale_date DESC LIMIT 10"


async def refine_data_with_ai(user_input, df, user_id: int = 1):
    """
    使用AI精炼数据,确定X轴和Y轴

    Args:
        user_input: 用户输入
        df: 查询结果DataFrame
        user_id: 用户ID,用于获取用户选择的模型配置

    Returns:
        精炼后的数据配置
    """
    system_prompt = (
        "Based on the user's question and the query result, determine the appropriate columns for the X-axis and Y-axis, "
        "as well as the scale and unit for displaying the data. The column names, scale, and unit should be returned in JSON format using markdown.\n\n"
        "User's question: {user_input}\n\n"
        "Query result:\n\n"
        f"{df.to_json(orient='records')}\n\n"
        "The JSON format should be as follows:\n\n"
        "```json\n"
        "{\n"
        '  "x_axis": "column_name",\n'
        '  "y_axes": ["column_name1", "column_name2", ...],\n'
        '  "scale": "linear",\n'
        '  "unit": "unit_name"\n'
        "}\n"
        "```"
    )

    ai_response = await call_configured_ai_model(system_prompt, user_input, user_id=user_id)
    if ai_response:
        json_start = ai_response.find("```json\n") + len("```json\n")
        json_end = ai_response.find("\n```", json_start)
        json_data = ai_response[json_start:json_end].strip()

        try:
            refined_data = json.loads(json_data)
            return refined_data
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析错误: {e}")
            return None
    else:
        logging.error("AI未能生成有效的回复")
        return None


async def generate_insight_analysis(user_input, df, user_id: int = 1):
    """
    生成数据洞察分析

    Args:
        user_input: 用户输入
        df: 查询结果DataFrame
        user_id: 用户ID,用于获取用户选择的模型配置

    Returns:
        洞察分析文本
    """
    # 动态获取当前时间信息
    from datetime import datetime
    import pytz

    # 获取中国时区的当前时间
    china_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(china_tz)
    current_date = current_time.strftime('%Y-%m-%d')
    current_year = current_time.year
    current_month = current_time.month

    system_prompt = (
        "基于用户的问题和查询结果，生成深入的洞察分析。分析应该简洁明了，并提供从数据中得出的有意义的见解。\n\n"
        f"当前时间上下文：今天是{current_date}，当前年份是{current_year}年{current_month}月\n"
        f"数据时间范围：2024年6月至12月\n\n"
        f"用户问题：{user_input}\n\n"
        f"查询结果：\n{df.to_json(orient='records', force_ascii=False)}\n\n"
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
        "请确保分析内容准确、有见地，并与用户的问题紧密相关。使用中文回答。"
    )

    ai_response = await call_configured_ai_model(system_prompt, user_input, user_id=user_id)
    if ai_response:
        # 直接返回AI响应，不再寻找特定格式标记
        # AI应该直接返回格式化的Markdown内容
        return ai_response.strip()
    else:
        logging.error("AI未能生成有效的洞察分析")
        return None


async def determine_chart_type(user_input, json_data, user_id: int = 1):
    """
    确定图表类型

    Args:
        user_input: 用户输入
        json_data: JSON格式的数据
        user_id: 用户ID,用于获取用户选择的模型配置

    Returns:
        图表类型
    """
    system_prompt = (
        "Based on the user's question and the provided data, determine the most appropriate chart type to visualize the data. "
        "The chart type should be returned as a string in markdown format.\n\n"
        "User's question: {user_input}\n\n"
        "Data:\n\n"
        f"{json_data}\n\n"
        "The chart type should be one of the following: 'bar', 'line', 'pie', 'scatter', 'histogram'.\n\n"
        "The response should be formatted as follows:\n\n"
        "```chart\n"
        "chart_type\n"
        "```"
    )

    ai_response = await call_configured_ai_model(system_prompt, user_input, user_id=user_id)
    if ai_response:
        chart_start = ai_response.find("```chart\n") + len("```chart\n")
        chart_end = ai_response.find("\n```", chart_start)
        chart_type = ai_response[chart_start:chart_end].strip()

        if chart_type in ["bar", "line", "pie", "scatter", "histogram"]:
            return chart_type
        else:
            logging.error("AI生成的图表类型无效")
            return None
    else:
        logging.error("AI未能生成有效的回复")
        return None
