"""
意图识别路由器(Intent Router)
用于分类用户输入的意图类型
支持从数据库读取AI模型配置
"""
from openai import AsyncOpenAI
from core.config import settings
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 全局客户端和配置缓存
_llm_client_cache = None
_llm_config_cache = None


async def _get_llm_config() -> Optional[Dict[str, Any]]:
    """从数据库获取用于意图识别的LLM配置"""
    global _llm_config_cache

    if _llm_config_cache:
        return _llm_config_cache

    try:
        from sqlalchemy import select
        from models.sys_ai_model_config import SysAiModelConfig
        from db.session import async_session

        async with async_session() as session:
            # 查询默认的chat模型配置
            result = await session.execute(
                select(SysAiModelConfig)
                .where(SysAiModelConfig.model_type == 'chat')
                .where(SysAiModelConfig.is_active == True)
                .where(SysAiModelConfig.is_default == True)
                .limit(1)
            )
            config = result.scalar_one_or_none()

            if config:
                _llm_config_cache = {
                    'provider': config.provider,
                    'model_name': config.model_name,
                    'api_url': config.api_url,
                    'api_key': config.api_key,
                    'model_params': config.model_params or {}
                }
                logger.info(f"从数据库加载意图识别模型配置: {config.model_name}")
                return _llm_config_cache

    except Exception as e:
        logger.warning(f"从数据库加载LLM配置失败: {e}")

    # 回退到环境变量配置
    if settings.OPENAI_API_KEY:
        _llm_config_cache = {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'api_url': 'https://api.openai.com/v1',
            'api_key': settings.OPENAI_API_KEY,
            'model_params': {}
        }
        logger.info("使用环境变量中的OpenAI配置")
        return _llm_config_cache

    logger.warning("未找到有效的LLM配置,意图识别将使用规则匹配")
    return None


async def _get_llm_client() -> Optional[AsyncOpenAI]:
    """获取LLM客户端(支持多种API提供商)"""
    global _llm_client_cache

    if _llm_client_cache:
        return _llm_client_cache

    config = await _get_llm_config()
    if not config:
        return None

    try:
        # 根据provider类型处理API URL
        # OpenAI SDK的行为: base_url + endpoint路径
        # 例如: base_url="https://api.openai.com/v1" -> 自动变成 "https://api.openai.com/v1/chat/completions"

        provider = config.get('provider', 'openai').lower()
        api_url = config['api_url'].rstrip('/')

        if provider == 'openai':
            # OpenAI标准: 配置应该是 https://api.openai.com/v1
            # SDK会自动添加 /chat/completions
            base_url = api_url if api_url.endswith('/v1') else api_url + '/v1'

        elif provider == 'siliconflow':
            # 硅基流动: 配置是完整URL https://api.siliconflow.cn/v1/chat/completions
            # 需要去掉endpoint部分,只保留到/v1
            if '/chat/completions' in api_url:
                base_url = api_url.split('/chat/completions')[0]
            elif '/embeddings' in api_url:
                base_url = api_url.split('/embeddings')[0]
            else:
                # 如果已经是base URL,确保以/v1结尾
                base_url = api_url if api_url.endswith('/v1') else api_url + '/v1'

        else:
            # 其他provider,默认处理方式
            # 移除可能存在的endpoint路径
            if '/chat/completions' in api_url:
                base_url = api_url.split('/chat/completions')[0]
            elif '/embeddings' in api_url:
                base_url = api_url.split('/embeddings')[0]
            else:
                base_url = api_url

            # 确保以/v1结尾(如果URL结构支持)
            if '/v1' in base_url and not base_url.endswith('/v1'):
                # 截取到/v1为止
                base_url = base_url[:base_url.index('/v1') + 3]
            elif not base_url.endswith('/v1') and not base_url.endswith('/api'):
                base_url = base_url + '/v1'

        _llm_client_cache = AsyncOpenAI(
            api_key=config['api_key'],
            base_url=base_url
        )
        logger.info(f"LLM客户端初始化成功: provider={provider}, base_url={base_url}")
        return _llm_client_cache

    except Exception as e:
        logger.error(f"LLM客户端初始化失败: {e}")
        return None


# 意图类型定义
class IntentType:
    CHITCHAT = "chitchat"  # 闲聊
    QUERY = "query"  # 数据查询
    VISUALIZATION = "visualization"  # 可视化请求
    HELP = "help"  # 帮助请求


# 闲聊关键词(规则匹配)
CHITCHAT_KEYWORDS = [
    '你好', 'hello', 'hi', '早上好', '下午好', '晚上好',
    '谢谢', 'thank', '再见', 'bye',
    '你是谁', '你叫什么', '介绍一下',
    '天气', '吃饭', '怎么样'
]

# 查询关键词
QUERY_KEYWORDS = [
    '多少', '统计', '查询', '查看', '显示', '列出',
    '总共', '数量', '数据', '记录', '信息',
    '最大', '最小', '平均', '求和', '计数',
    'count', 'sum', 'average', 'max', 'min',
    'show', 'list', 'find', 'get'
]

# 可视化关键词
VIZ_KEYWORDS = [
    '图表', '可视化', '画', '绘制', '展示',
    '柱状图', '折线图', '饼图', '散点图',
    'chart', 'plot', 'graph', 'visualize',
    'bar', 'line', 'pie', 'scatter'
]


async def classify_intent(user_input: str) -> Dict[str, Any]:
    """
    分类用户输入的意图

    Args:
        user_input: 用户输入文本

    Returns:
        {
            "intent": "chitchat/query/visualization/help",
            "confidence": 0.9,
            "reason": "匹配原因"
        }
    """
    # 首先尝试规则匹配(快速路径)
    rule_result = classify_by_rules(user_input)
    if rule_result and rule_result['confidence'] > 0.8:
        logger.info(f"规则匹配意图: {rule_result['intent']} (confidence: {rule_result['confidence']})")
        return rule_result

    # 尝试使用LLM分类(从数据库读取配置)
    llm_client = await _get_llm_client()
    if llm_client:
        try:
            llm_result = await classify_by_llm(user_input, llm_client)
            logger.info(f"LLM分类意图: {llm_result['intent']} (confidence: {llm_result['confidence']})")
            return llm_result
        except Exception as e:
            logger.warning(f"LLM意图分类失败,回退到规则匹配: {e}")

    # 回退到规则匹配
    if rule_result:
        return rule_result

    # 默认返回query意图
    return {
        "intent": IntentType.QUERY,
        "confidence": 0.5,
        "reason": "默认query意图"
    }


def classify_by_rules(user_input: str) -> Dict[str, Any]:
    """
    基于规则的意图分类

    Args:
        user_input: 用户输入

    Returns:
        意图分类结果
    """
    user_input_lower = user_input.lower().strip()

    # 检查闲聊
    chitchat_score = sum(1 for kw in CHITCHAT_KEYWORDS if kw in user_input_lower)
    if chitchat_score > 0 and len(user_input) < 20:
        return {
            "intent": IntentType.CHITCHAT,
            "confidence": min(0.8 + chitchat_score * 0.1, 0.95),
            "reason": f"匹配闲聊关键词: {chitchat_score}个"
        }

    # 检查帮助
    if any(kw in user_input_lower for kw in ['帮助', 'help', '怎么用', '如何使用']):
        return {
            "intent": IntentType.HELP,
            "confidence": 0.9,
            "reason": "匹配帮助关键词"
        }

    # 检查可视化
    viz_score = sum(1 for kw in VIZ_KEYWORDS if kw in user_input_lower)
    if viz_score > 0:
        return {
            "intent": IntentType.VISUALIZATION,
            "confidence": min(0.7 + viz_score * 0.1, 0.9),
            "reason": f"匹配可视化关键词: {viz_score}个"
        }

    # 检查查询
    query_score = sum(1 for kw in QUERY_KEYWORDS if kw in user_input_lower)
    if query_score > 0:
        return {
            "intent": IntentType.QUERY,
            "confidence": min(0.7 + query_score * 0.05, 0.85),
            "reason": f"匹配查询关键词: {query_score}个"
        }

    # 如果包含问号,很可能是查询
    if '?' in user_input or '?' in user_input:
        return {
            "intent": IntentType.QUERY,
            "confidence": 0.7,
            "reason": "包含问号"
        }

    # 默认query
    return {
        "intent": IntentType.QUERY,
        "confidence": 0.6,
        "reason": "默认分类"
    }


async def classify_by_llm(user_input: str, llm_client: AsyncOpenAI) -> Dict[str, Any]:
    """
    使用LLM进行意图分类

    Args:
        user_input: 用户输入
        llm_client: LLM客户端

    Returns:
        意图分类结果
    """
    system_prompt = """你是一个意图分类器。请判断用户输入属于以下哪种类型:

1. **chitchat** - 闲聊: 打招呼、寒暄、感谢等非任务相关的对话
   例如: "你好", "谢谢", "你是谁", "天气怎么样"

2. **query** - 数据查询: 需要查询数据库、统计分析的问题
   例如: "有多少用户", "最近一周的销售额是多少", "显示前10条记录"

3. **visualization** - 可视化: 明确要求生成图表的请求
   例如: "画一个销售趋势图", "用柱状图展示", "可视化用户分布"

4. **help** - 帮助: 询问如何使用系统
   例如: "怎么用", "有什么功能", "帮助"

请以JSON格式返回: {"intent": "类型", "confidence": 0-1之间的置信度, "reason": "判断理由"}"""

    # 获取模型配置
    config = await _get_llm_config()
    model_name = config['model_name'] if config else 'gpt-4o-mini'

    try:
        response = await llm_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=150
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # 验证结果格式
        if 'intent' not in result or result['intent'] not in [
            IntentType.CHITCHAT,
            IntentType.QUERY,
            IntentType.VISUALIZATION,
            IntentType.HELP
        ]:
            raise ValueError(f"无效的intent: {result.get('intent')}")

        # 确保confidence在0-1之间
        if 'confidence' not in result:
            result['confidence'] = 0.7
        result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))

        if 'reason' not in result:
            result['reason'] = "LLM分类"

        return result

    except json.JSONDecodeError as e:
        logger.error(f"LLM返回的JSON解析失败: {e}")
        raise
    except Exception as e:
        logger.error(f"LLM意图分类失败: {e}")
        raise


async def should_use_dataset(user_input: str, intent: str) -> bool:
    """
    判断是否应该查询用户上传的数据集

    策略:
        - chitchat/help -> False (不查询数据集)
        - query/visualization -> True (可能需要查询数据集)

    Args:
        user_input: 用户输入
        intent: 意图类型

    Returns:
        是否应该使用数据集
    """
    if intent in [IntentType.CHITCHAT, IntentType.HELP]:
        return False

    # 对于query和visualization,尝试检索相关列
    # 如果找到相关列,则使用数据集;否则使用固定Schema
    from services.embedding_service import search_relevant_columns

    try:
        relevant_cols = await search_relevant_columns(user_input, top_k=3)

        # 如果找到相似度>0.7的列,认为应该使用数据集
        if relevant_cols and relevant_cols[0]['similarity'] > 0.7:
            logger.info(f"检测到相关数据集列: {relevant_cols[0]['col_name']} (similarity: {relevant_cols[0]['similarity']:.3f})")
            return True

    except Exception as e:
        logger.warning(f"检索数据集列失败: {e}")

    # 默认返回False,使用固定Schema
    return False
