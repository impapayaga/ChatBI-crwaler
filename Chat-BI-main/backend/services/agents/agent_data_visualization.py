"""
数据可视化判断Agent

智能判断查询结果数据应该以什么形式展示：
- chart: 图表（柱状图、折线图、饼图等）
- table: 表格
- card: 卡片（政策详情、产品详情等包含长文本的单条记录）
- text: 纯文本回答
"""
import logging
import pandas as pd
from typing import Dict, Any, Literal, Optional
from api.utils.ai_utils import call_configured_ai_model

logger = logging.getLogger(__name__)

# 可视化类型枚举
VisualizationType = Literal["chart", "table", "card", "text"]


async def judge_visualization_type(
    user_input: str,
    df: pd.DataFrame,
    user_id: int = 1
) -> Dict[str, Any]:
    """
    判断数据应该使用什么方式展示

    工作流程：
    1. 快速规则判断（高置信度场景）
    2. AI智能判断（复杂场景）
    3. 降级保护（失败时返回安全默认值）

    Args:
        user_input: 用户输入的问题
        df: 查询结果DataFrame
        user_id: 用户ID，用于获取AI模型配置

    Returns:
        {
            "visualization_type": "chart" | "table" | "card" | "text",
            "reason": "判断理由",
            "confidence": 0.95,
            "metadata": {...}  # 额外元数据，如推荐的图表类型
        }
    """
    logger.info(f"开始判断数据可视化类型: 用户问题='{user_input}', 数据形状={df.shape}")

    # 步骤1: 快速规则判断
    rule_result = _apply_quick_rules(user_input, df)
    if rule_result["confidence"] >= 0.9:
        logger.info(f"规则引擎高置信度判断: {rule_result['visualization_type']} ({rule_result['confidence']})")
        return rule_result

    # 步骤2: AI智能判断
    try:
        ai_result = await _ai_intelligent_judge(user_input, df, user_id)
        if ai_result["confidence"] >= 0.7:
            logger.info(f"AI智能判断: {ai_result['visualization_type']} ({ai_result['confidence']})")
            return ai_result
    except Exception as e:
        logger.error(f"AI判断失败: {e}")

    # 步骤3: 降级保护 - 返回规则判断结果
    logger.warning(f"AI判断失败或置信度不足，降级使用规则判断: {rule_result['visualization_type']}")
    return rule_result


def _apply_quick_rules(user_input: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    基于规则的快速判断

    规则优先级：
    1. 空数据 -> text
    2. 单行长文本 -> card
    3. 多行数值数据 -> chart
    4. 多列或全文本 -> table
    """
    row_count = len(df)
    col_count = len(df.columns)

    # 规则1: 空数据
    if row_count == 0:
        return {
            "visualization_type": "text",
            "reason": "查询结果为空",
            "confidence": 1.0,
            "metadata": {}
        }

    # 规则2: 单行多列的详细信息（如政策详情、产品详情）
    if row_count == 1 and col_count >= 3:
        # 检查是否有长文本列（超过100字符）
        has_long_text = any(
            isinstance(val, str) and len(val) > 100
            for val in df.iloc[0].values
        )
        if has_long_text:
            return {
                "visualization_type": "card",
                "reason": "单条记录包含详细文本信息，适合卡片展示",
                "confidence": 0.95,
                "metadata": {
                    "fields": df.columns.tolist()
                }
            }

    # 规则3: 多行数值数据（适合图表）
    if row_count >= 2 and row_count <= 100:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()

        # 至少有1个数值列和1个分类列
        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            return {
                "visualization_type": "chart",
                "reason": f"包含{len(numeric_cols)}个数值列和{len(categorical_cols)}个分类列，适合图表展示",
                "confidence": 0.85,
                "metadata": {
                    "numeric_columns": numeric_cols,
                    "categorical_columns": categorical_cols,
                    "suggested_chart_type": _suggest_chart_type(row_count, len(numeric_cols))
                }
            }

    # 规则4: 多行纯数值数据
    if row_count >= 2 and len(df.select_dtypes(include=['number']).columns) >= 2:
        return {
            "visualization_type": "chart",
            "reason": "多行数值数据，适合趋势或对比图表",
            "confidence": 0.8,
            "metadata": {
                "suggested_chart_type": "line" if row_count > 10 else "bar"
            }
        }

    # 规则5: 超过10列或者超过100行 -> 表格
    if col_count > 10 or row_count > 100:
        return {
            "visualization_type": "table",
            "reason": f"数据量较大({row_count}行{col_count}列)，适合表格展示",
            "confidence": 0.9,
            "metadata": {}
        }

    # 规则6: 全是文本数据 -> 表格
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) == 0:
        return {
            "visualization_type": "table",
            "reason": "数据全部为文本，适合表格展示",
            "confidence": 0.85,
            "metadata": {}
        }

    # 默认: 表格展示（保守策略）
    return {
        "visualization_type": "table",
        "reason": "默认使用表格展示",
        "confidence": 0.6,
        "metadata": {}
    }


def _suggest_chart_type(row_count: int, numeric_col_count: int) -> str:
    """
    根据数据特征推荐图表类型
    """
    if row_count <= 5:
        return "bar"  # 少量数据用柱状图
    elif row_count > 20:
        return "line"  # 大量数据用折线图看趋势
    elif numeric_col_count == 1:
        return "bar"  # 单个指标用柱状图
    else:
        return "bar"  # 多个指标用堆叠柱状图


async def _ai_intelligent_judge(
    user_input: str,
    df: pd.DataFrame,
    user_id: int
) -> Dict[str, Any]:
    """
    使用AI进行智能判断

    适用于规则难以覆盖的复杂场景
    """
    # 构建数据摘要
    data_summary = _build_data_summary(df)

    system_prompt = """你是一个数据可视化专家Agent，负责判断查询结果数据应该用什么方式展示给用户。

展示方式选项：
1. **chart** (图表): 数值型数据，有趋势、对比、占比等关系，用柱状图、折线图、饼图等
2. **table** (表格): 多行多列的结构化数据列表
3. **card** (卡片): 单条或少量记录的详细信息展示，适合政策详情、产品描述等长文本内容
4. **text** (纯文本): 简单的文本回答

判断标准：
- 政策文本、文章内容、详细描述 → card
- 时间序列数据、数值对比、统计分析 → chart
- 列表型的多条记录、明细查询 → table
- 简单问答、提示信息 → text

请返回JSON格式（必须用markdown包裹）：
```json
{
  "visualization_type": "chart/table/card/text",
  "reason": "选择此展示方式的理由",
  "confidence": 0.95,
  "metadata": {
    "suggested_chart_type": "bar/line/pie"
  }
}
```"""

    user_prompt = f"""用户问题: {user_input}

数据摘要:
- 形状: {data_summary['shape']}
- 列名: {', '.join(data_summary['columns'])}
- 数据类型: {data_summary['dtypes']}
- 样本数据:
{data_summary['sample_preview']}

请判断应该用什么方式展示这些数据？"""

    try:
        ai_response = await call_configured_ai_model(
            system_prompt,
            user_prompt,
            user_id=user_id
        )

        # 解析AI返回的JSON
        result = _parse_ai_response(ai_response)

        # 验证结果有效性
        if result and result.get("visualization_type") in ["chart", "table", "card", "text"]:
            # 确保置信度在合理范围内
            result["confidence"] = min(max(result.get("confidence", 0.8), 0.0), 1.0)
            return result
        else:
            raise ValueError(f"AI返回了无效的visualization_type: {result.get('visualization_type')}")

    except Exception as e:
        logger.error(f"AI智能判断失败: {e}")
        raise


def _build_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    构建数据摘要供AI分析
    """
    # 获取样本数据（前3行）
    sample_df = df.head(3)
    sample_preview = sample_df.to_string(index=False, max_colwidth=50)

    return {
        "shape": f"{len(df)}行 × {len(df.columns)}列",
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_preview": sample_preview
    }


def _parse_ai_response(ai_response: str) -> Optional[Dict[str, Any]]:
    """
    解析AI返回的JSON响应
    """
    import json

    try:
        # 提取JSON代码块
        json_start = ai_response.find("```json\n")
        if json_start == -1:
            json_start = ai_response.find("```json")

        if json_start != -1:
            json_start = ai_response.find("\n", json_start) + 1
            json_end = ai_response.find("\n```", json_start)
            if json_end == -1:
                json_end = ai_response.find("```", json_start)

            json_data = ai_response[json_start:json_end].strip()
        else:
            # 没有markdown包裹，尝试直接解析
            json_data = ai_response.strip()

        result = json.loads(json_data)

        # 确保必需字段存在
        if "visualization_type" not in result:
            logger.error(f"AI响应缺少visualization_type字段: {result}")
            return None

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}, 原始响应: {ai_response[:200]}")
        return None
    except Exception as e:
        logger.error(f"解析AI响应时出错: {e}")
        return None
