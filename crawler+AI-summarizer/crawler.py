import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from database import PolicyFile, get_db
from sqlalchemy.orm import Session
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.keywords = ["人工智能", "医疗器械", "生物医药"]
        
    def contains_keywords(self, text):
        """检查文本是否包含关键词"""
        if not text:
            return False, []
        found_keywords = []
        for keyword in self.keywords:
            if keyword in text:
                found_keywords.append(keyword)
        return len(found_keywords) > 0, found_keywords
    
    def crawl_beijing_policies(self, db: Session, max_pages=10):
        """爬取北京市政府政策文件 - 支持翻页"""
        logger.info("开始爬取北京市政府政策文件...")
        
        # 构建分页URL列表
        base_urls = []
        base_url = "https://www.beijing.gov.cn/zhengce/zhengcefagui/"
        base_urls.append(base_url)  # 第一页
        
        # 添加其他页面
        for i in range(2, max_pages + 1):
            if i == 2:
                page_url = base_url + "index_2.html"
            else:
                page_url = base_url + f"index_{i}.html"
            base_urls.append(page_url)
        
        policies_found = 0
        
        try:
            for base_url in base_urls:
                try:
                    logger.info(f"正在爬取: {base_url}")
                    response = self.session.get(base_url, timeout=30)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找所有链接
                    all_links = soup.find_all('a', href=True)
                    logger.info(f"北京市网站找到 {len(all_links)} 个链接")
                    
                    # 查找包含关键词的链接
                    for link in all_links:
                        try:
                            title = link.get_text(strip=True)
                            href = link.get('href', '')
                            
                            if not title or not href:
                                continue
                            
                            # 检查是否包含关键词
                            has_keywords, found_keywords = self.contains_keywords(title)
                            if not has_keywords:
                                continue
                            
                            # 构建完整URL
                            if href.startswith('/'):
                                full_url = "https://www.beijing.gov.cn" + href
                            elif href.startswith('http'):
                                full_url = href
                            else:
                                full_url = base_url + href
                            
                            # 检查是否已存在
                            existing = db.query(PolicyFile).filter(
                                PolicyFile.url == full_url
                            ).first()
                            if existing:
                                continue
                            
                            # 获取详细信息
                            try:
                                detail_response = self.session.get(full_url, timeout=30)
                                detail_response.encoding = 'utf-8'
                                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                                
                                # 提取发布日期和发布单位
                                publish_date = ""
                                publish_unit = ""
                                
                                # 获取页面文本内容
                                page_text = detail_soup.get_text()
                                
                                # 查找日期信息 - 改进正则表达式
                                date_patterns = [
                                    r'发布日期[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
                                    r'发布时间[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
                                    r'发文时间[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
                                    r'(\d{4}年\d{1,2}月\d{1,2}日)',
                                    r'(\d{4}-\d{1,2}-\d{1,2})',
                                    r'(\d{4}/\d{1,2}/\d{1,2})'
                                ]
                                
                                for pattern in date_patterns:
                                    try:
                                        date_match = re.search(pattern, page_text)
                                        if date_match:
                                            publish_date = date_match.group(1)
                                            # 标准化日期格式
                                            if '年' in publish_date and '月' in publish_date and '日' in publish_date:
                                                # 转换 2024年1月1日 为 2024-01-01
                                                import re as re2
                                                date_parts = re2.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日', publish_date)
                                                if date_parts:
                                                    year, month, day = date_parts[0]
                                                    publish_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                            break
                                    except:
                                        continue
                                
                                # 查找发布单位 - 改进正则表达式和提取逻辑
                                unit_patterns = [
                                    r'发布单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'发文机关[：:]\s*([^\n\r，,。；;]+)',
                                    r'发文机构[：:]\s*([^\n\r，,。；;]+)',
                                    r'发布机构[：:]\s*([^\n\r，,。；;]+)',
                                    r'制定机关[：:]\s*([^\n\r，,。；;]+)',
                                    r'起草单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'主办单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'承办单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'北京市[^，,。\n\r]{2,30}(?:委员会|局|厅|办公室|政府|部门)',
                                    r'北京市[^，,。\n\r]{2,30}委员会',
                                    r'北京市[^，,。\n\r]{2,30}局',
                                    r'北京市[^，,。\n\r]{2,30}厅',
                                    r'北京市[^，,。\n\r]{2,30}办公室'
                                ]
                                
                                for pattern in unit_patterns:
                                    try:
                                        unit_match = re.search(pattern, page_text)
                                        if unit_match:
                                            publish_unit = unit_match.group(1).strip()
                                            # 清理单位名称
                                            publish_unit = re.sub(r'[：:]\s*$', '', publish_unit)
                                            if len(publish_unit) > 3:  # 确保单位名称有意义
                                                break
                                    except:
                                        continue
                                
                                # 如果还没找到发布单位，尝试从标题中提取
                                if not publish_unit:
                                    title_patterns = [
                                        r'北京市[^，,。\n\r]{2,30}(?:委员会|局|厅|办公室|政府|部门)',
                                        r'北京市[^，,。\n\r]{2,30}委员会',
                                        r'北京市[^，,。\n\r]{2,30}局',
                                        r'北京市[^，,。\n\r]{2,30}厅',
                                        r'北京市[^，,。\n\r]{2,30}办公室'
                                    ]
                                    
                                    for pattern in title_patterns:
                                        try:
                                            unit_match = re.search(pattern, title)
                                            if unit_match:
                                                publish_unit = unit_match.group(0).strip()
                                                break
                                        except:
                                            continue
                                
                                # 提取内容
                                content = detail_soup.get_text()
                                
                                # 保存到数据库
                                policy = PolicyFile(
                                    title=title,
                                    source="北京市政府",
                                    url=full_url,
                                    publish_date=publish_date,
                                    publish_unit=publish_unit,
                                    content=content[:5000],  # 限制内容长度
                                    keywords_found=','.join(found_keywords)
                                )
                                db.add(policy)
                                policies_found += 1
                                logger.info(f"找到政策文件: {title}")
                                
                            except Exception as e:
                                logger.warning(f"获取详情失败 {full_url}: {e}")
                                continue
                            
                            time.sleep(1)  # 避免请求过快
                            
                        except Exception as e:
                            logger.warning(f"处理政策项失败: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"爬取北京市政府页面失败: {e}")
                    continue
            
            db.commit()
            logger.info(f"北京市政府爬取完成，新增 {policies_found} 条政策")
            return policies_found
            
        except Exception as e:
            logger.error(f"爬取北京市政府失败: {e}")
            return 0
    
    def crawl_guangdong_policies(self, db: Session, max_pages=10):
        """爬取广东省政府政策文件 - 动态爬取政策文件列表页面"""
        logger.info("开始爬取广东省政府政策文件...")
        
        # 使用分页URL来获取更多政策文件
        base_urls = [
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_2.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_3.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_4.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_5.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_6.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_7.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_8.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_9.html",
            "https://www.gd.gov.cn/zwgk/wjk/qbwj/index_10.html"
        ]
        
        policies_found = 0
        
        for base_url in base_urls:
            try:
                logger.info(f"正在爬取: {base_url}")
                response = self.session.get(base_url, timeout=30)
                
                # 使用更健壮的编码处理
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    logger.info("成功解析广东省网站内容")
                except Exception as e:
                    logger.error(f"解析广东省网站失败: {e}")
                    continue
                
                # 查找所有链接
                all_links = soup.find_all('a', href=True)
                logger.info(f"广东省网站找到 {len(all_links)} 个链接")
                
                # 查找包含关键词的链接
                for link in all_links:
                    try:
                        title = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        if not title or not href:
                            continue
                        
                        # 检查是否包含关键词
                        has_keywords, found_keywords = self.contains_keywords(title)
                        if not has_keywords:
                            continue
                        
                        logger.info(f"找到包含关键词的链接: {title}")
                        logger.info(f"关键词: {found_keywords}")
                        logger.info(f"URL: {href}")
                        
                        # 构建完整URL
                        if href.startswith('/'):
                            full_url = "https://www.gd.gov.cn" + href
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            full_url = base_url.replace('/index.html', '') + '/' + href
                        
                        # 检查是否已存在
                        existing = db.query(PolicyFile).filter(
                            PolicyFile.url == full_url
                        ).first()
                        if existing:
                            continue
                        
                        # 提取发布日期和发布单位
                        publish_date = ""
                        publish_unit = ""
                        
                        # 从链接文本中提取日期 - 更精确的日期匹配
                        date_patterns = [
                            r'(\d{4}年\d{1,2}月\d{1,2}日)',  # 2024年1月1日
                            r'(\d{4}-\d{1,2}-\d{1,2})',      # 2024-01-01
                            r'(\d{4}\.\d{1,2}\.\d{1,2})',    # 2024.01.01
                        ]
                        
                        for pattern in date_patterns:
                            date_match = re.search(pattern, title)
                            if date_match:
                                publish_date = date_match.group(1)
                                # 标准化日期格式
                                if '年' in publish_date and '月' in publish_date and '日' in publish_date:
                                    # 转换 2024年1月1日 为 2024-01-01
                                    import re as re2
                                    date_parts = re2.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日', publish_date)
                                    if date_parts:
                                        year, month, day = date_parts[0]
                                        publish_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                break
                        
                        # 如果没有找到日期，尝试从URL中提取
                        if not publish_date:
                            url_date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', full_url)
                            if url_date_match:
                                year, month, day = url_date_match.groups()
                                publish_date = f"{year}-{month}-{day}"
                        
                        # 如果还是没有日期，尝试从网页内容中提取
                        if not publish_date:
                            try:
                                response = self.session.get(full_url, timeout=30)
                                response.encoding = response.apparent_encoding or 'utf-8'
                                content_soup = BeautifulSoup(response.content, 'html.parser')
                                content_text = content_soup.get_text()
                                
                                # 从网页内容中查找日期
                                content_date_patterns = [
                                    r'发布日期[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
                                    r'发布时间[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
                                    r'发文时间[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
                                    r'(\d{4}年\d{1,2}月\d{1,2}日)',
                                    r'(\d{4}-\d{1,2}-\d{1,2})',
                                    r'(\d{4}/\d{1,2}/\d{1,2})'
                                ]
                                
                                for pattern in content_date_patterns:
                                    date_match = re.search(pattern, content_text)
                                    if date_match:
                                        publish_date = date_match.group(1)
                                        # 标准化日期格式
                                        if '年' in publish_date and '月' in publish_date and '日' in publish_date:
                                            import re as re2
                                            date_parts = re2.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日', publish_date)
                                            if date_parts:
                                                year, month, day = date_parts[0]
                                                publish_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                        break
                            except:
                                pass
                        
                        # 如果还是没有日期，使用当前日期作为默认值
                        if not publish_date:
                            publish_date = "2024-01-01"
                        
                        # 更精确的发布单位提取
                        # 首先尝试从标题中提取
                        if '广东省人民政府办公厅' in title:
                            publish_unit = "广东省人民政府办公厅"
                        elif '广东省人民政府' in title:
                            publish_unit = "广东省人民政府"
                        elif '粤府' in title:
                            publish_unit = "广东省人民政府"
                        elif '粤府办' in title:
                            publish_unit = "广东省人民政府办公厅"
                        else:
                            # 如果标题中没有，尝试从网页内容中提取
                            try:
                                response = self.session.get(full_url, timeout=30)
                                response.encoding = response.apparent_encoding or 'utf-8'
                                content_soup = BeautifulSoup(response.content, 'html.parser')
                                content_text = content_soup.get_text()
                                
                                # 从网页内容中查找发布单位 - 改进正则表达式
                                unit_patterns = [
                                    r'发布单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'发文机关[：:]\s*([^\n\r，,。；;]+)',
                                    r'发文机构[：:]\s*([^\n\r，,。；;]+)',
                                    r'发布机构[：:]\s*([^\n\r，,。；;]+)',
                                    r'制定机关[：:]\s*([^\n\r，,。；;]+)',
                                    r'起草单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'主办单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'承办单位[：:]\s*([^\n\r，,。；;]+)',
                                    r'广东省[^，,。\n\r]{2,30}(?:委员会|局|厅|办公室|政府|部门)',
                                    r'广东省[^，,。\n\r]{2,30}委员会',
                                    r'广东省[^，,。\n\r]{2,30}局',
                                    r'广东省[^，,。\n\r]{2,30}厅',
                                    r'广东省[^，,。\n\r]{2,30}办公室'
                                ]
                                
                                for pattern in unit_patterns:
                                    try:
                                        unit_match = re.search(pattern, content_text)
                                        if unit_match:
                                            publish_unit = unit_match.group(1).strip()
                                            break
                                    except:
                                        continue
                                        
                                # 如果还是没有找到，使用默认值
                                if not publish_unit:
                                    publish_unit = "广东省政府"
                                    
                            except Exception as e:
                                logger.error(f"获取广东省政策详情失败: {e}")
                                publish_unit = "广东省政府"
                        
                        # 提取政策内容
                        content = title  # 暂时只保存标题，后续可以获取详细内容
                        
                        # 保存到数据库
                        policy = PolicyFile(
                            title=title,
                            source="广东省政府",
                            url=full_url,
                            publish_date=publish_date,
                            publish_unit=publish_unit,
                            content=content,
                            keywords_found=','.join(found_keywords)
                        )
                        db.add(policy)
                        policies_found += 1
                        logger.info(f"找到广东省政策文件: {title}")
                        
                        time.sleep(0.5)  # 避免请求过快
                        
                    except Exception as e:
                        logger.warning(f"处理政策项失败: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"爬取广东省政府失败: {e}")
                continue
        
        if policies_found == 0:
            logger.info("没有找到包含目标关键词的广东省政策文件")
        
        db.commit()
        logger.info(f"广东省政府爬取完成，新增 {policies_found} 条政策")
        return policies_found
    
    def crawl_all_policies(self, db: Session):
        """爬取所有政策文件"""
        total_found = 0
        total_found += self.crawl_beijing_policies(db)
        total_found += self.crawl_guangdong_policies(db)
        return total_found
