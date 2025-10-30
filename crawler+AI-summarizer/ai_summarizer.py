import httpx
import json
from typing import List, Dict
from database import PolicyFile, AISummary, get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class AISummarizer:
    def __init__(self):
        self.api_key = "sk-htjoiirxczzfbhbanimwmwmlmhafzthacgubydjjpmtwbseo"
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = "Qwen/Qwen2.5-7B-Instruct"  # 使用可用的模型
        
    def create_summary_prompt(self, policy: PolicyFile) -> str:
        """创建AI总结的提示词"""
        prompt = f"""
请对以下政策文件进行结构化总结，要求包含以下五个方面：

政策文件信息：
- 文件名称：{policy.title}
- 发布单位：{policy.publish_unit or '未知'}
- 发布日期：{policy.publish_date or '未知'}
- 来源网站：{policy.source}
- 原始链接：{policy.url}
- 政策内容：{policy.content[:2000] if policy.content else '无详细内容'}

请按照以下格式输出JSON结果：
{{
    "title": "政策文件名称",
    "publish_unit": "发布单位",
    "publish_date": "发布日期",
    "summary": "政策摘要内容总结（200-300字，重点突出与人工智能、医疗器械、生物医药相关的内容）",
    "url": "超链接网址"
}}

重要要求：
1. **发布单位提取**：请仔细从政策内容中提取真实的发布单位，格式如"XX省人民政府"、"XX市人民政府"、"XX部"、"XX厅"等，不要使用"未知"或"模拟发布单位"
2. **发布日期提取**：请从政策内容中提取真实的发布日期，格式如"2024年X月X日"、"2024-XX-XX"等，不要使用"未知"或"模拟日期"
3. **政策摘要内容总结**：要突出与人工智能、医疗器械、生物医药相关的内容
4. **如果政策内容不相关**：请说明"该政策文件与人工智能、医疗器械、生物医药领域关联度较低"
5. **保持信息的准确性和客观性**
6. **输出必须是有效的JSON格式**

特别注意：
- 如果政策内容中包含明确的发布单位和日期信息，请直接提取使用
- 如果无法从内容中提取到准确信息，publish_unit和publish_date字段请保持原值不变
- 不要编造或猜测发布单位和日期信息
"""
        return prompt
    
    def call_ai_api(self, prompt: str) -> str:
        """调用AI API进行总结"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, json=data)
                
                if response.status_code != 200:
                    logger.error(f"AI API返回错误: {response.status_code}, 响应: {response.text}")
                    return None
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"AI API调用失败: {e}")
            return None
    
    def parse_ai_response(self, response: str) -> Dict:
        """解析AI响应"""
        try:
            # 尝试提取JSON部分
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                # 如果没有找到JSON，返回默认格式
                return {
                    "title": "解析失败",
                    "publish_unit": "未知",
                    "publish_date": "未知",
                    "summary": f"AI总结失败，原始响应：{response[:200]}",
                    "url": ""
                }
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            return {
                "title": "解析失败",
                "publish_unit": "未知",
                "publish_date": "未知",
                "summary": f"AI总结失败，原始响应：{response[:200]}",
                "url": ""
            }
    
    def summarize_policy(self, policy: PolicyFile) -> AISummary:
        """对单个政策文件进行AI总结"""
        logger.info(f"开始总结政策文件: {policy.title}")
        
        # 创建提示词
        prompt = self.create_summary_prompt(policy)
        
        # 调用AI API
        ai_response = self.call_ai_api(prompt)
        if not ai_response:
            logger.error(f"AI API调用失败: {policy.title}")
            return None
        
        # 解析响应
        summary_data = self.parse_ai_response(ai_response)
        
        # 创建AI总结记录
        ai_summary = AISummary(
            policy_id=policy.id,
            title=summary_data.get("title", policy.title),
            publish_unit=summary_data.get("publish_unit", policy.publish_unit or "未知"),
            publish_date=summary_data.get("publish_date", policy.publish_date or "未知"),
            summary=summary_data.get("summary", "总结生成失败"),
            url=summary_data.get("url", policy.url)
        )
        
        return ai_summary
    
    def process_unprocessed_policies(self, db: Session) -> int:
        """处理未总结的政策文件"""
        logger.info("开始处理未总结的政策文件...")
        
        # 获取未处理的政策文件
        unprocessed_policies = db.query(PolicyFile).filter(
            PolicyFile.is_processed == False
        ).all()
        
        processed_count = 0
        for policy in unprocessed_policies:
            try:
                # 生成AI总结
                ai_summary = self.summarize_policy(policy)
                if ai_summary:
                    # 检查是否已存在相同的总结
                    existing_summary = db.query(AISummary).filter(
                        AISummary.policy_id == policy.id
                    ).first()
                    
                    if not existing_summary:
                        db.add(ai_summary)
                        # 标记为已处理
                        policy.is_processed = True
                        processed_count += 1
                        logger.info(f"成功总结政策: {policy.title}")
                    else:
                        policy.is_processed = True
                        logger.info(f"政策已存在总结: {policy.title}")
                
            except Exception as e:
                logger.error(f"总结政策失败 {policy.title}: {e}")
                continue
        
        db.commit()
        logger.info(f"AI总结处理完成，新增 {processed_count} 条总结")
        return processed_count
