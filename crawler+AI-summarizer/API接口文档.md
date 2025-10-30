# 政策文件智能分析系统 - API接口文档

## 🔗 基础信息

**API服务地址**: `http://localhost:8000`  
**API文档地址**: `http://localhost:8000/docs` (Swagger UI)  
**API版本**: v1.0.0  
**数据格式**: JSON  

## 📡 接口列表

### 1. 获取政策文件列表
**接口地址**: `GET /api/policies`  
**功能**: 获取所有爬取的政策文件数据  
**请求参数**: 
- `source` (可选): 数据来源筛选，支持 "北京市政府" 或 "广东省政府"
- `limit` (可选): 返回数量限制，默认100

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
    "content": "政策文件内容...",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

**字段说明**:
- `id`: 政策文件唯一标识
- `title`: 政策文件标题
- `source`: 数据来源（北京市政府/广东省政府）
- `url`: 政策文件原文链接
- `publish_date`: 发布日期
- `publish_unit`: 发布单位
- `keywords_found`: 匹配的关键词
- `content`: 政策文件内容
- `created_at`: 数据创建时间

### 1.1. 获取北京市政府政策文件
**接口地址**: `GET /api/policies/beijing`  
**功能**: 专门获取北京市政府的政策文件  
**请求参数**: 
- `limit` (可选): 返回数量限制，默认100

### 1.2. 获取广东省政府政策文件
**接口地址**: `GET /api/policies/guangdong`  
**功能**: 专门获取广东省政府的政策文件  
**请求参数**: 
- `limit` (可选): 返回数量限制，默认100

### 2. 获取AI总结列表
**接口地址**: `GET /api/summaries`  
**功能**: 获取AI智能总结的数据  
**请求参数**: 
- `source` (可选): 数据来源筛选，支持 "北京市政府" 或 "广东省政府"
- `limit` (可选): 返回数量限制，默认100

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

**字段说明**:
- `id`: AI总结唯一标识
- `title`: 政策文件标题
- `publish_unit`: 发布单位
- `publish_date`: 发布日期
- `summary`: AI生成的总结内容
- `url`: 政策文件原文链接
- `created_at`: 总结创建时间

### 2.1. 获取北京市政府AI总结
**接口地址**: `GET /api/summaries/beijing`  
**功能**: 专门获取北京市政府的AI总结  
**请求参数**: 
- `limit` (可选): 返回数量限制，默认100

### 2.2. 获取广东省政府AI总结
**接口地址**: `GET /api/summaries/guangdong`  
**功能**: 专门获取广东省政府的AI总结  
**请求参数**: 
- `limit` (可选): 返回数量限制，默认100

### 3. 获取统计信息
**接口地址**: `GET /api/stats`  
**功能**: 获取系统数据统计信息  
**请求参数**: 无  

**响应示例**:
```json
{
  "total_policies": 23,
  "total_summaries": 22,
  "beijing_policies": 19,
  "guangdong_policies": 4
}
```

**字段说明**:
- `total_policies`: 总政策文件数量
- `total_summaries`: 总AI总结数量
- `beijing_policies`: 北京政策文件数量
- `guangdong_policies`: 广东政策文件数量

### 4. 启动爬取任务
**接口地址**: `POST /api/crawl`  
**功能**: 手动触发政策文件爬取任务  
**请求参数**: 无  

**响应示例**:
```json
{
  "success": true,
  "message": "爬取完成，新增 5 条政策文件",
  "total_found": 5
}
```

**字段说明**:
- `success`: 操作是否成功
- `message`: 操作结果消息
- `total_found`: 新增的政策文件数量

### 5. 启动AI总结任务
**接口地址**: `POST /api/summarize`  
**功能**: 手动触发AI总结任务  
**请求参数**: 无  

**响应示例**:
```json
{
  "success": true,
  "message": "AI总结完成，新增 3 条总结",
  "processed_count": 3
}
```

**字段说明**:
- `success`: 操作是否成功
- `message`: 操作结果消息
- `processed_count`: 处理的政策文件数量

## 🔧 前端集成示例

### JavaScript 调用示例
```javascript
// 基础配置
const API_BASE = 'http://localhost:8000/api';

// 获取政策文件列表
async function getPolicies() {
    try {
        const response = await fetch(`${API_BASE}/policies`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('获取政策文件失败:', error);
        throw error;
    }
}

// 获取AI总结列表
async function getSummaries() {
    try {
        const response = await fetch(`${API_BASE}/summaries`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('获取AI总结失败:', error);
        throw error;
    }
}

// 获取统计信息
async function getStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('获取统计信息失败:', error);
        throw error;
    }
}

// 启动爬取任务
async function startCrawl() {
    try {
        const response = await fetch(`${API_BASE}/crawl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('启动爬取失败:', error);
        throw error;
    }
}

// 启动AI总结任务
async function startSummarize() {
    try {
        const response = await fetch(`${API_BASE}/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('启动AI总结失败:', error);
        throw error;
    }
}
```

### React 组件示例
```jsx
import React, { useState, useEffect } from 'react';

const PolicyAnalysis = () => {
    const [policies, setPolicies] = useState([]);
    const [summaries, setSummaries] = useState([]);
    const [stats, setStats] = useState({});
    const [loading, setLoading] = useState(false);

    const API_BASE = 'http://localhost:8000/api';

    // 加载数据
    const loadData = async () => {
        setLoading(true);
        try {
            const [policiesRes, summariesRes, statsRes] = await Promise.all([
                fetch(`${API_BASE}/policies`),
                fetch(`${API_BASE}/summaries`),
                fetch(`${API_BASE}/stats`)
            ]);

            const policiesData = await policiesRes.json();
            const summariesData = await summariesRes.json();
            const statsData = await statsRes.json();

            setPolicies(policiesData);
            setSummaries(summariesData);
            setStats(statsData);
        } catch (error) {
            console.error('加载数据失败:', error);
        } finally {
            setLoading(false);
        }
    };

    // 启动爬取
    const handleCrawl = async () => {
        try {
            const response = await fetch(`${API_BASE}/crawl`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            alert(result.message);
            loadData(); // 重新加载数据
        } catch (error) {
            console.error('爬取失败:', error);
            alert('爬取失败');
        }
    };

    // 启动AI总结
    const handleSummarize = async () => {
        try {
            const response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            alert(result.message);
            loadData(); // 重新加载数据
        } catch (error) {
            console.error('AI总结失败:', error);
            alert('AI总结失败');
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    if (loading) return <div>加载中...</div>;

    return (
        <div>
            <h1>政策文件智能分析系统</h1>
            
            {/* 统计信息 */}
            <div className="stats">
                <h2>统计信息</h2>
                <p>总政策文件: {stats.total_policies}</p>
                <p>AI总结数量: {stats.total_summaries}</p>
                <p>北京政策: {stats.beijing_policies}</p>
                <p>广东政策: {stats.guangdong_policies}</p>
            </div>

            {/* 操作按钮 */}
            <div className="actions">
                <button onClick={handleCrawl}>开始爬取</button>
                <button onClick={handleSummarize}>AI总结</button>
                <button onClick={loadData}>刷新数据</button>
            </div>

            {/* 政策文件列表 */}
            <div className="policies">
                <h2>政策文件列表</h2>
                {policies.map(policy => (
                    <div key={policy.id} className="policy-item">
                        <h3>{policy.title}</h3>
                        <p>发布单位: {policy.publish_unit}</p>
                        <p>发布日期: {policy.publish_date}</p>
                        <p>来源: {policy.source}</p>
                        <p>关键词: {policy.keywords_found}</p>
                        <a href={policy.url} target="_blank" rel="noopener noreferrer">
                            查看原文
                        </a>
                    </div>
                ))}
            </div>

            {/* AI总结列表 */}
            <div className="summaries">
                <h2>AI总结列表</h2>
                {summaries.map(summary => (
                    <div key={summary.id} className="summary-item">
                        <h3>{summary.title}</h3>
                        <p>发布单位: {summary.publish_unit}</p>
                        <p>发布日期: {summary.publish_date}</p>
                        <p>AI总结: {summary.summary}</p>
                        <a href={summary.url} target="_blank" rel="noopener noreferrer">
                            查看原文
                        </a>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PolicyAnalysis;
```

### Vue 组件示例
```vue
<template>
  <div class="policy-analysis">
    <h1>政策文件智能分析系统</h1>
    
    <!-- 统计信息 -->
    <div class="stats">
      <h2>统计信息</h2>
      <p>总政策文件: {{ stats.total_policies }}</p>
      <p>AI总结数量: {{ stats.total_summaries }}</p>
      <p>北京政策: {{ stats.beijing_policies }}</p>
      <p>广东政策: {{ stats.guangdong_policies }}</p>
    </div>

    <!-- 操作按钮 -->
    <div class="actions">
      <button @click="handleCrawl">开始爬取</button>
      <button @click="handleSummarize">AI总结</button>
      <button @click="loadData">刷新数据</button>
    </div>

    <!-- 政策文件列表 -->
    <div class="policies">
      <h2>政策文件列表</h2>
      <div v-for="policy in policies" :key="policy.id" class="policy-item">
        <h3>{{ policy.title }}</h3>
        <p>发布单位: {{ policy.publish_unit }}</p>
        <p>发布日期: {{ policy.publish_date }}</p>
        <p>来源: {{ policy.source }}</p>
        <p>关键词: {{ policy.keywords_found }}</p>
        <a :href="policy.url" target="_blank" rel="noopener noreferrer">
          查看原文
        </a>
      </div>
    </div>

    <!-- AI总结列表 -->
    <div class="summaries">
      <h2>AI总结列表</h2>
      <div v-for="summary in summaries" :key="summary.id" class="summary-item">
        <h3>{{ summary.title }}</h3>
        <p>发布单位: {{ summary.publish_unit }}</p>
        <p>发布日期: {{ summary.publish_date }}</p>
        <p>AI总结: {{ summary.summary }}</p>
        <a :href="summary.url" target="_blank" rel="noopener noreferrer">
          查看原文
        </a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PolicyAnalysis',
  data() {
    return {
      policies: [],
      summaries: [],
      stats: {},
      loading: false
    };
  },
  methods: {
    async loadData() {
      this.loading = true;
      try {
        const API_BASE = 'http://localhost:8000/api';
        
        const [policiesRes, summariesRes, statsRes] = await Promise.all([
          fetch(`${API_BASE}/policies`),
          fetch(`${API_BASE}/summaries`),
          fetch(`${API_BASE}/stats`)
        ]);

        this.policies = await policiesRes.json();
        this.summaries = await summariesRes.json();
        this.stats = await statsRes.json();
      } catch (error) {
        console.error('加载数据失败:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async handleCrawl() {
      try {
        const response = await fetch('http://localhost:8000/api/crawl', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        alert(result.message);
        this.loadData();
      } catch (error) {
        console.error('爬取失败:', error);
        alert('爬取失败');
      }
    },
    
    async handleSummarize() {
      try {
        const response = await fetch('http://localhost:8000/api/summarize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        alert(result.message);
        this.loadData();
      } catch (error) {
        console.error('AI总结失败:', error);
        alert('AI总结失败');
      }
    }
  },
  
  mounted() {
    this.loadData();
  }
};
</script>
```

## 🚀 后端启动说明

### 启动API服务
```bash
# 启动后端API服务
python main.py --mode api
```

**服务地址**: `http://localhost:8000`  
**API文档**: `http://localhost:8000/docs` (自动生成的Swagger文档)

### 健康检查
```bash
# 检查服务是否正常运行
curl http://localhost:8000/api/stats
```

## 📝 注意事项

1. **CORS设置**: 后端已配置CORS，支持跨域请求
2. **数据格式**: 所有接口返回JSON格式数据
3. **错误处理**: 前端需要处理网络错误和API错误
4. **实时更新**: 建议前端定期刷新数据或使用WebSocket（如需要）
5. **数据缓存**: 建议前端实现数据缓存机制

## 🔧 开发环境配置

### 后端环境要求
- Python 3.8+
- 依赖包: `pip install -r requirements.txt`
- 数据库: SQLite (自动创建)

### 前端环境要求
- 支持ES6+的现代浏览器
- 支持fetch API
- 建议使用现代前端框架 (React/Vue/Angular)

---

