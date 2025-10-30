# API调用示例文档

## 🚀 后端启动

### 启动API服务
```bash
# 方法一：使用启动脚本
start.bat

# 方法二：命令行启动
python main.py --mode api
```

**服务地址**: `http://localhost:8000`  
**API文档**: `http://localhost:8000/docs`

## 📡 API接口调用

### 1. 获取政策文件列表
```javascript
// JavaScript调用 - 获取所有政策文件
async function getPolicies() {
    const response = await fetch('http://localhost:8000/api/policies');
    const data = await response.json();
    return data;
}

// 获取北京市政府政策文件
async function getBeijingPolicies() {
    const response = await fetch('http://localhost:8000/api/policies/beijing');
    const data = await response.json();
    return data;
}

// 获取广东省政府政策文件
async function getGuangdongPolicies() {
    const response = await fetch('http://localhost:8000/api/policies/guangdong');
    const data = await response.json();
    return data;
}
```

```python
# Python调用
import requests

def get_policies():
    response = requests.get('http://localhost:8000/api/policies')
    return response.json()

def get_beijing_policies():
    response = requests.get('http://localhost:8000/api/policies/beijing')
    return response.json()

def get_guangdong_policies():
    response = requests.get('http://localhost:8000/api/policies/guangdong')
    return response.json()
```

**响应示例**:
```json
[
    {
        "id": 1,
        "title": "北京市加快人工智能基础科学研究发展行动计划（2025-2027年）",
        "source": "北京市政府",
        "url": "https://www.beijing.gov.cn/zhengce/zhengcefagui/./202507/t20250722_4154767.html",
        "publish_date": "2025年7月4日",
        "publish_unit": "北京市科学技术委员会",
        "keywords_found": "人工智能",
        "content": "政策内容...",
        "created_at": "2024-01-01T00:00:00"
    }
]
```

### 2. 获取AI总结列表
```javascript
// JavaScript调用 - 获取所有AI总结
async function getSummaries() {
    const response = await fetch('http://localhost:8000/api/summaries');
    const data = await response.json();
    return data;
}

// 获取北京市政府AI总结
async function getBeijingSummaries() {
    const response = await fetch('http://localhost:8000/api/summaries/beijing');
    const data = await response.json();
    return data;
}

// 获取广东省政府AI总结
async function getGuangdongSummaries() {
    const response = await fetch('http://localhost:8000/api/summaries/guangdong');
    const data = await response.json();
    return data;
}
```

```python
# Python调用
def get_summaries():
    response = requests.get('http://localhost:8000/api/summaries')
    return response.json()

def get_beijing_summaries():
    response = requests.get('http://localhost:8000/api/summaries/beijing')
    return response.json()

def get_guangdong_summaries():
    response = requests.get('http://localhost:8000/api/summaries/guangdong')
    return response.json()
```

**响应示例**:
```json
[
    {
        "id": 1,
        "title": "北京市加快人工智能基础科学研究发展行动计划（2025-2027年）",
        "publish_unit": "北京市科学技术委员会",
        "publish_date": "2025年7月4日",
        "summary": "该行动计划旨在通过人工智能基础科学研究，推动北京在全球范围内形成具有影响力的AI创新源...",
        "url": "https://www.beijing.gov.cn/zhengce/zhengcefagui/./202507/t20250722_4154767.html",
        "created_at": "2024-01-01T00:00:00"
    }
]
```

### 3. 获取统计信息
```javascript
// JavaScript调用
async function getStats() {
    const response = await fetch('http://localhost:8000/api/stats');
    const data = await response.json();
    return data;
}
```

```python
# Python调用
def get_stats():
    response = requests.get('http://localhost:8000/api/stats')
    return response.json()
```

**响应示例**:
```json
{
    "total_policies": 23,
    "total_summaries": 22,
    "beijing_policies": 19,
    "guangdong_policies": 4
}
```

### 4. 启动爬取任务
```javascript
// JavaScript调用
async function startCrawl() {
    const response = await fetch('http://localhost:8000/api/crawl', {
        method: 'POST'
    });
    const data = await response.json();
    return data;
}
```

```python
# Python调用
def start_crawl():
    response = requests.post('http://localhost:8000/api/crawl')
    return response.json()
```

**响应示例**:
```json
{
    "success": true,
    "message": "爬取完成，新增 5 条政策文件",
    "total_found": 5
}
```

### 5. 启动AI总结任务
```javascript
// JavaScript调用
async function startSummarize() {
    const response = await fetch('http://localhost:8000/api/summarize', {
        method: 'POST'
    });
    const data = await response.json();
    return data;
}
```

```python
# Python调用
def start_summarize():
    response = requests.post('http://localhost:8000/api/summarize')
    return response.json()
```

**响应示例**:
```json
{
    "success": true,
    "message": "AI总结完成，新增 3 条总结",
    "processed_count": 3
}
```

## 🔧 完整的前端集成示例

### HTML + JavaScript 完整示例
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>政策文件分析系统</title>
</head>
<body>
    <div id="app">
        <h1>政策文件分析系统</h1>
        <button onclick="loadData()">加载数据</button>
        <button onclick="startCrawl()">开始爬取</button>
        <button onclick="startSummarize()">AI总结</button>
        <div id="stats"></div>
        <div id="policies"></div>
        <div id="summaries"></div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000/api';
        
        // 加载统计数据
        async function loadStats() {
            try {
                const response = await fetch(`${API_BASE}/stats`);
                const stats = await response.json();
                document.getElementById('stats').innerHTML = `
                    <h2>统计信息</h2>
                    <p>总政策文件: ${stats.total_policies}</p>
                    <p>AI总结数量: ${stats.total_summaries}</p>
                    <p>北京政策: ${stats.beijing_policies}</p>
                    <p>广东政策: ${stats.guangdong_policies}</p>
                `;
            } catch (error) {
                console.error('加载统计信息失败:', error);
            }
        }
        
        // 加载政策文件
        async function loadPolicies() {
            try {
                const response = await fetch(`${API_BASE}/policies`);
                const policies = await response.json();
                let html = '<h2>政策文件列表</h2>';
                policies.forEach(policy => {
                    html += `
                        <div style="border: 1px solid #ccc; margin: 10px; padding: 10px;">
                            <h3>${policy.title}</h3>
                            <p>发布单位: ${policy.publish_unit}</p>
                            <p>发布日期: ${policy.publish_date}</p>
                            <p>来源: ${policy.source}</p>
                            <p>关键词: ${policy.keywords_found}</p>
                            <a href="${policy.url}" target="_blank">查看原文</a>
                        </div>
                    `;
                });
                document.getElementById('policies').innerHTML = html;
            } catch (error) {
                console.error('加载政策文件失败:', error);
            }
        }
        
        // 加载AI总结
        async function loadSummaries() {
            try {
                const response = await fetch(`${API_BASE}/summaries`);
                const summaries = await response.json();
                let html = '<h2>AI总结列表</h2>';
                summaries.forEach(summary => {
                    html += `
                        <div style="border: 1px solid #ccc; margin: 10px; padding: 10px;">
                            <h3>${summary.title}</h3>
                            <p>发布单位: ${summary.publish_unit}</p>
                            <p>发布日期: ${summary.publish_date}</p>
                            <p>AI总结: ${summary.summary}</p>
                            <a href="${summary.url}" target="_blank">查看原文</a>
                        </div>
                    `;
                });
                document.getElementById('summaries').innerHTML = html;
            } catch (error) {
                console.error('加载AI总结失败:', error);
            }
        }
        
        // 加载所有数据
        async function loadData() {
            await loadStats();
            await loadPolicies();
            await loadSummaries();
        }
        
        // 启动爬取
        async function startCrawl() {
            try {
                const response = await fetch(`${API_BASE}/crawl`, { method: 'POST' });
                const result = await response.json();
                alert(result.message);
                loadData(); // 重新加载数据
            } catch (error) {
                console.error('爬取失败:', error);
                alert('爬取失败');
            }
        }
        
        // 启动AI总结
        async function startSummarize() {
            try {
                const response = await fetch(`${API_BASE}/summarize`, { method: 'POST' });
                const result = await response.json();
                alert(result.message);
                loadData(); // 重新加载数据
            } catch (error) {
                console.error('AI总结失败:', error);
                alert('AI总结失败');
            }
        }
        
        // 页面加载时自动加载数据
        window.onload = loadData;
    </script>
</body>
</html>
```

## 🐍 Python 完整集成示例

```python
import requests
import json
from datetime import datetime

class PolicyAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
    
    def get_policies(self):
        """获取政策文件列表"""
        response = requests.get(f"{self.api_base}/policies")
        return response.json()
    
    def get_beijing_policies(self):
        """获取北京市政府政策文件"""
        response = requests.get(f"{self.api_base}/policies/beijing")
        return response.json()
    
    def get_guangdong_policies(self):
        """获取广东省政府政策文件"""
        response = requests.get(f"{self.api_base}/policies/guangdong")
        return response.json()
    
    def get_summaries(self):
        """获取AI总结列表"""
        response = requests.get(f"{self.api_base}/summaries")
        return response.json()
    
    def get_beijing_summaries(self):
        """获取北京市政府AI总结"""
        response = requests.get(f"{self.api_base}/summaries/beijing")
        return response.json()
    
    def get_guangdong_summaries(self):
        """获取广东省政府AI总结"""
        response = requests.get(f"{self.api_base}/summaries/guangdong")
        return response.json()
    
    def get_stats(self):
        """获取统计信息"""
        response = requests.get(f"{self.api_base}/stats")
        return response.json()
    
    def start_crawl(self):
        """启动爬取任务"""
        response = requests.post(f"{self.api_base}/crawl")
        return response.json()
    
    def start_summarize(self):
        """启动AI总结任务"""
        response = requests.post(f"{self.api_base}/summarize")
        return response.json()
    
    def display_policies(self):
        """显示政策文件"""
        policies = self.get_policies()
        print(f"找到 {len(policies)} 条政策文件:")
        for policy in policies:
            print(f"- {policy['title']}")
            print(f"  发布单位: {policy['publish_unit']}")
            print(f"  发布日期: {policy['publish_date']}")
            print(f"  来源: {policy['source']}")
            print(f"  关键词: {policy['keywords_found']}")
            print()
    
    def display_summaries(self):
        """显示AI总结"""
        summaries = self.get_summaries()
        print(f"找到 {len(summaries)} 条AI总结:")
        for summary in summaries:
            print(f"- {summary['title']}")
            print(f"  发布单位: {summary['publish_unit']}")
            print(f"  发布日期: {summary['publish_date']}")
            print(f"  AI总结: {summary['summary'][:100]}...")
            print()
    
    def display_stats(self):
        """显示统计信息"""
        stats = self.get_stats()
        print("=== 统计信息 ===")
        print(f"总政策文件: {stats['total_policies']}")
        print(f"AI总结数量: {stats['total_summaries']}")
        print(f"北京政策: {stats['beijing_policies']}")
        print(f"广东政策: {stats['guangdong_policies']}")
        print()

# 使用示例
if __name__ == "__main__":
    client = PolicyAPIClient()
    
    # 显示统计信息
    client.display_stats()
    
    # 显示所有政策文件
    client.display_policies()
    
    # 显示北京市政府政策文件
    beijing_policies = client.get_beijing_policies()
    print(f"北京市政府政策文件: {len(beijing_policies)} 条")
    
    # 显示广东省政府政策文件
    guangdong_policies = client.get_guangdong_policies()
    print(f"广东省政府政策文件: {len(guangdong_policies)} 条")
    
    # 显示所有AI总结
    client.display_summaries()
    
    # 显示北京市政府AI总结
    beijing_summaries = client.get_beijing_summaries()
    print(f"北京市政府AI总结: {len(beijing_summaries)} 条")
    
    # 显示广东省政府AI总结
    guangdong_summaries = client.get_guangdong_summaries()
    print(f"广东省政府AI总结: {len(guangdong_summaries)} 条")
    
    # 启动爬取（可选）
    # result = client.start_crawl()
    # print(f"爬取结果: {result}")
    
    # 启动AI总结（可选）
    # result = client.start_summarize()
    # print(f"总结结果: {result}")
```

## 🔧 错误处理

### 常见错误码
- **200**: 请求成功
- **404**: 接口不存在
- **500**: 服务器内部错误

### 错误处理示例
```javascript
async function safeApiCall(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('API调用失败:', error);
        return { success: false, error: error.message };
    }
}

// 使用示例
async function loadData() {
    const result = await safeApiCall('http://localhost:8000/api/policies');
    if (result.success) {
        console.log('数据加载成功:', result.data);
    } else {
        console.error('数据加载失败:', result.error);
    }
}
```

## 📊 数据格式说明

### 政策文件数据格式
```json
{
    "id": 1,
    "title": "政策文件标题",
    "source": "北京市政府",
    "url": "https://...",
    "publish_date": "2024-01-01",
    "publish_unit": "发布单位",
    "keywords_found": "关键词",
    "content": "政策内容",
    "created_at": "2024-01-01T00:00:00"
}
```

### AI总结数据格式
```json
{
    "id": 1,
    "title": "政策文件标题",
    "publish_unit": "发布单位",
    "publish_date": "2024-01-01",
    "summary": "AI生成的总结内容",
    "url": "https://...",
    "created_at": "2024-01-01T00:00:00"
}
```

### 统计信息数据格式
```json
{
    "total_policies": 23,
    "total_summaries": 22,
    "beijing_policies": 19,
    "guangdong_policies": 4
}
```

---

**注意**: 确保后端服务已启动（`python main.py --mode api`）后再调用API接口。
