# 技术文档

## 1. 数据采集策略

### 1.1 采集流程

```
用户输入关键词
    ↓
创建采集任务（task_id）
    ↓
并行采集三个平台
    ├─ Reddit
    ├─ YouTube
    └─ Twitter
    ↓
保存原始数据到数据库
    ├─ reddit_submission
    ├─ youtube_video
    └─ twitter_tweet
    ↓
数据清洗（按 task_id 过滤）
    ↓
保存到 cleaned_data 表
    ↓
AI 分析（MapReduce）
    ↓
生成分析报告
```

### 1.2 Reddit 采集策略

**技术方案**：使用 Reddit 官方 JSON API

**优点**：
- 无需认证
- 稳定可靠
- 返回结构化数据

**实现代码**：
```python
def fetch_reddit(keyword, limit=30, language="en"):
    url = "https://www.reddit.com/search.json"
    params = {
        "q": keyword,
        "limit": limit,
        "sort": "relevance"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 ..."
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    data = response.json()
    
    posts = []
    for child in data["data"]["children"]:
        post = child["data"]
        posts.append({
            "post_id": post["id"],
            "title": post["title"],
            "subreddit": post["subreddit"],
            "score": post["score"],
            "num_comments": post["num_comments"],
            "created_utc": post["created_utc"],
            "url": f"https://reddit.com{post['permalink']}"
        })
    
    return posts
```

**关键点**：
- 使用 `search.json` 端点
- 设置合理的 User-Agent
- 处理分页和限制

### 1.3 YouTube 采集策略

**技术方案**：使用 `youtube-search-python` 库 + `youtube-transcript-api`

**优点**：
- 无需 API Key
- 可以获取字幕
- 简单易用

**实现代码**：
```python
def fetch_youtube(keyword, limit=10, language="en"):
    results = YoutubeSearch(keyword, max_results=limit).to_dict()
    
    videos = []
    for r in results:
        videos.append({
            "video_id": r["id"],
            "title": r["title"],
            "channel": r["channel"],
            "published_at": r.get("publish_time", ""),
            "view_count": parse_view_count(r.get("views", "0")),
            "url": "https://www.youtube.com" + r["url_suffix"],
            "transcript": ""
        })
    
    return videos

def fetch_transcripts(videos, lang='en'):
    for v in videos:
        try:
            transcript_obj = YouTubeTranscriptApi.list_transcripts(v["video_id"])
            # 优先手动字幕
            try:
                t = transcript_obj.find_manually_created_transcript([lang])
            except:
                t = transcript_obj.find_generated_transcript([lang])
            
            transcript_list = t.fetch()
            v["transcript"] = " ".join([x["text"] for x in transcript_list])
        except:
            v["transcript"] = ""
    
    return videos
```

**关键点**：
- 解析观看次数（处理 K、M 等单位）
- 优先获取手动字幕
- 处理无字幕情况

### 1.4 Twitter 采集策略

**技术方案**：Nitter 镜像站 + Selenium 备选

**主要方案：Nitter**

Nitter 是 Twitter 的开源前端，提供无需认证的访问。

```python
def fetch_twitter(keyword, limit=30, language="en"):
    instances = [
        "nitter.poast.org",
        "nitter.privacyredirect.com",
        "nitter.tiekoetter.com"
    ]
    
    tweets = []
    
    for instance in instances:
        if len(tweets) >= limit:
            break
        
        url = f"https://{instance}/search"
        params = {"q": keyword, "l": language}
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select(".timeline-item")
            
            for item in items:
                # 提取推文内容
                content_el = item.select_one(".tweet-content")
                content = content_el.get_text(strip=True)
                
                # 提取用户名
                username_el = item.select_one(".username")
                username = username_el.get_text(strip=True)
                
                # 提取统计数据
                # ...
                
                tweets.append({
                    "tweet_id": tweet_id,
                    "content": content,
                    "username": username,
                    "created_at": created_at,
                    "retweet_count": retweet_count,
                    "like_count": like_count,
                    "url": f"https://twitter.com{tweet_path}"
                })
            
            if tweets:
                break  # 成功则停止尝试其他实例
        except:
            continue
    
    return tweets
```

**备选方案：Selenium**

```python
if not tweets and SELENIUM_AVAILABLE:
    from twitter_scraper_selenium import fetch_twitter_selenium
    tweets = fetch_twitter_selenium(keyword, limit)
```

**关键点**：
- 镜像站轮询（提高成功率）
- HTML 解析（BeautifulSoup）
- Selenium 作为最后备选

### 1.5 数据清洗策略

**目标**：统一数据格式，去除噪音

**实现代码**：
```python
def process_data(keyword="unknown", task_ids=None):
    # 1. 按 task_ids 过滤数据（关键！）
    if task_ids:
        task_filter = f"WHERE task_id IN ({','.join(map(str, task_ids))})"
    else:
        task_filter = ""
    
    # 2. 读取三个平台的数据
    reddit_df = pd.read_sql_query(f"SELECT * FROM reddit_submission {task_filter}", conn)
    youtube_df = pd.read_sql_query(f"SELECT * FROM youtube_video {task_filter}", conn)
    twitter_df = pd.read_sql_query(f"SELECT * FROM twitter_tweet {task_filter}", conn)
    
    # 3. 统一字段名
    reddit_df = reddit_df.rename(columns={
        'post_id': 'raw_id',
        'title': 'content',
        'subreddit': 'author',
        'created_utc': 'raw_time'
    })
    
    # 4. 合并数据
    all_data = pd.concat([reddit_df, youtube_df, twitter_df])
    
    # 5. 清洗文本
    all_data['content'] = all_data['content'].apply(clean_text)
    
    # 6. 标准化时间
    all_data['timestamp'] = all_data['raw_time'].apply(normalize_time)
    
    # 7. 去重
    all_data = all_data.drop_duplicates(subset=['platform', 'raw_id'])
    
    # 8. 添加关键词标签
    all_data['keyword'] = keyword
    
    # 9. 保存到数据库
    all_data.to_sql('cleaned_data', conn, if_exists='append', index=False)
```

**清洗规则**：
```python
def clean_text(text):
    # 1. HTML 实体解码
    text = html.unescape(text)
    
    # 2. 移除 URL
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # 3. 保留中英文、数字、标点
    text = re.sub(r'[^\w\s\u4e00-\u9fa5,.!?，。！？]', '', text)
    
    # 4. 规范化空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

**关键改进**：
- **按 task_ids 过滤**：只处理当前任务的数据，避免旧数据污染
- **统一格式**：三个平台的数据统一为相同结构
- **去重**：基于 platform + raw_id 去重

## 2. AI Prompt 设计

### 2.1 MapReduce 架构

为了控制 token 消耗，采用 MapReduce 架构：

```
原始数据（可能很多）
    ↓
采样（最多 100 条）
    ↓
分批（每批 4000 tokens）
    ↓
Map 阶段：并行分析每批
    ├─ 批次1 → 情感得分 + 观点
    ├─ 批次2 → 情感得分 + 观点
    └─ 批次3 → 情感得分 + 观点
    ↓
Reduce 阶段：汇总所有批次
    ↓
最终报告
```

### 2.2 Map 阶段 Prompt

**目标**：分析单个批次，提取情感和观点

**中文 Prompt**：
```python
prompt = f"""
你是一个专业的数据分析师，请分析以下社交媒体评论批次。

任务：
1. 给出整体情感得分（0-100）
2. 提取核心观点或争议点（最多 5 条）
3. 判断是否仍包含明显垃圾信息

待分析文本：
\"\"\"
{batch}
\"\"\"

请仅返回合法 JSON：
{{
  "sentiment_score": 75,
  "key_points": ["观点1", "观点2"],
  "spam_info": "无"
}}
"""
```

**关键点**：
- 明确任务目标
- 限制输出格式（JSON）
- 控制观点数量（最多 5 条）

### 2.3 Reduce 阶段 Prompt

**目标**：汇总所有批次，生成最终报告

**中文 Prompt**：
```python
topic_name = keyword if keyword else "主题"

prompt = f"""
你是高级舆情分析专家，请基于以下关于"{topic_name}"的观点完成最终汇总。

观点列表：
\"\"\"
{points_text}
\"\"\"

任务：
1. 总结 3 个关于 {topic_name} 的主要争议点
2. 生成一段 150-200 字关于 {topic_name} 的通俗摘要
3. 生成一个简洁的 Mermaid.js 思维导图（graph TD），最多 8 个节点，以"{topic_name}"作为根节点
4. 为每个节点标注情感倾向

思维导图要求：
- 根节点必须是：A[{topic_name}]
- 使用简短节点名（每个节点最多 10 个字）
- 最多 8 个节点
- 格式：graph TD; A[{topic_name}] --> B[观点1]; A --> C[观点2]; B --> D[细节];
- 保持简洁清晰

节点情感标注：
- 判断每个节点（除主题外）的情感倾向
- 返回格式：{{"节点ID": "positive/neutral/negative"}}
- 示例：{{"B": "positive", "C": "negative", "D": "neutral"}}

请仅返回合法 JSON：
{{
  "final_controversies": ["争议点1", "争议点2", "争议点3"],
  "human_summary": "关于 {topic_name} 的摘要内容",
  "mermaid_graph": "graph TD; A[{topic_name}] --> B[观点1]; A --> C[观点2];",
  "node_sentiments": {{"B": "positive", "C": "negative"}}
}}
"""
```

**关键改进**：
- **明确使用关键词**：在 prompt 中多次强调关键词
- **根节点固定**：`A[{keyword}]` 确保思维导图以关键词为中心
- **限制节点数量**：最多 8 个节点，避免过于复杂
- **情感标注**：为每个节点标注情感，用于前端可视化

### 2.4 Token 控制策略

**采样控制**：
```python
SAMPLE_SIZE = 100  # 最多采样 100 条

if len(df) > SAMPLE_SIZE:
    df = df.sample(SAMPLE_SIZE, random_state=42)
```

**分批策略**：
```python
MAX_TOKENS_PER_BATCH = 4000

batches = []
current_batch = ""
current_tokens = 0

for text in df["content"].tolist():
    tokens = get_token_count(text)
    
    if current_tokens + tokens > MAX_TOKENS_PER_BATCH:
        batches.append(current_batch.strip())
        current_batch = text
        current_tokens = tokens
    else:
        current_batch += "\n" + text
        current_tokens += tokens
```

**Token 计算**：
```python
import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")

def get_token_count(text: str) -> int:
    return len(ENCODING.encode(text))
```

## 3. 遇到的问题及解决方案

### 3.1 数据隔离问题

**问题**：不同关键词的数据混在一起

**原因**：`process_data()` 读取了所有历史数据，并标记成新关键词

**解决方案**：
```python
# 修改前：读取所有数据
reddit_df = pd.read_sql_query("SELECT * FROM reddit_submission", conn)

# 修改后：只读取指定任务的数据
def process_data(keyword="unknown", task_ids=None):
    if task_ids:
        task_filter = f"WHERE task_id IN ({','.join(map(str, task_ids))})"
    else:
        task_filter = ""
    
    reddit_df = pd.read_sql_query(
        f"SELECT * FROM reddit_submission {task_filter}", 
        conn
    )
```

**详细文档**：`DATA_ISOLATION_BUG_FIX.md`

### 3.2 分析报告覆盖问题

**问题**：新关键词的分析会覆盖旧关键词的报告

**原因**：所有关键词共用一个 `analysis_report.json` 文件

**解决方案**：
```python
# 修改前：固定文件名
with open("analysis_report.json", "w") as f:
    json.dump(final_report, f)

# 修改后：按关键词命名
if keyword:
    report_file = f"analysis_report_{keyword}.json"
else:
    report_file = "analysis_report.json"

with open(report_file, "w") as f:
    json.dump(final_report, f)
```

**API 读取也要修改**：
```python
# api.py
if keyword:
    report_file = f"analysis_report_{keyword}.json"
else:
    report_file = REPORT_FILE

if os.path.exists(report_file):
    with open(report_file, "r") as f:
        report = json.load(f)
```

**详细文档**：`REPORT_ISOLATION_FIX.md`

### 3.3 前端页面不刷新问题

**问题**：切换到源数据页面时，显示的是旧数据

**原因**：Flutter 使用页面缓存，切换标签时不重新创建页面

**解决方案**：
```dart
// 修改前：页面缓存
class _MainNavigationState extends State<MainNavigation> {
  final List<Widget> _pages = [
    DashboardPage(),
    SourceDataPage(),
    SubscriptionPage(),
  ];
  
  Widget build(BuildContext context) {
    return Scaffold(body: _pages[_selectedIndex]);
  }
}

// 修改后：动态创建
class _MainNavigationState extends State<MainNavigation> {
  Widget _getPage(int index) {
    switch (index) {
      case 0: return DashboardPage();
      case 1: return SourceDataPage();
      case 2: return SubscriptionPage();
    }
  }
  
  Widget build(BuildContext context) {
    return Scaffold(body: _getPage(_selectedIndex));
  }
}
```

**详细文档**：`SOURCE_DATA_UPDATE_FIX.md`

### 3.4 思维导图观点不相关问题

**问题**：思维导图的观点与关键词无关

**原因**：AI Prompt 中没有明确强调关键词

**解决方案**：
```python
# 修改前：泛泛的 prompt
prompt = "请生成思维导图"

# 修改后：明确使用关键词
topic_name = keyword if keyword else "主题"
prompt = f"""
任务：
1. 总结 3 个关于 {topic_name} 的主要争议点
2. 生成关于 {topic_name} 的摘要
3. 生成思维导图，根节点必须是：A[{topic_name}]
"""
```

### 3.5 Twitter 采集不稳定问题

**问题**：Twitter 采集经常失败

**原因**：单个 Nitter 实例不稳定

**解决方案**：
```python
# 镜像站轮询
instances = [
    "nitter.poast.org",
    "nitter.privacyredirect.com",
    "nitter.tiekoetter.com"
]

for instance in instances:
    try:
        # 尝试采集
        if success:
            break
    except:
        continue  # 尝试下一个

# Selenium 备选
if not tweets and SELENIUM_AVAILABLE:
    tweets = fetch_twitter_selenium(keyword, limit)
```

### 3.6 Flutter Web 平台检测问题

**问题**：`Platform.isWindows` 在 Web 上报错

**原因**：`dart:io` 的 Platform 类在 Web 上不可用

**解决方案**：
```dart
// 修改前
import 'dart:io';
if (Platform.isWindows) { ... }

// 修改后
import 'package:flutter/foundation.dart';
if (kIsWeb) {
  // Web 平台逻辑
} else {
  // 桌面/移动平台逻辑
}
```

### 3.7 DashboardData 模型缺少字段问题

**问题**：前端编译错误，`keyword` 字段不存在

**原因**：后端 API 返回了 `keyword` 字段，但前端模型没有定义

**解决方案**：
```dart
// 添加 keyword 字段
class DashboardData {
  final String keyword;
  
  DashboardData({
    ...
    this.keyword = '',
  });
  
  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      ...
      keyword: json['keyword'] as String? ?? '',
    );
  }
}
```

## 4. 性能优化

### 4.1 数据库索引

```sql
CREATE INDEX idx_keyword ON cleaned_data(keyword);
CREATE INDEX idx_task_id ON reddit_submission(task_id);
CREATE INDEX idx_task_id ON youtube_video(task_id);
CREATE INDEX idx_task_id ON twitter_tweet(task_id);
```

### 4.2 采集并行化

```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    reddit_future = executor.submit(fetch_reddit, keyword, limit)
    youtube_future = executor.submit(fetch_youtube, keyword, limit)
    twitter_future = executor.submit(fetch_twitter, keyword, limit)
    
    reddit_posts = reddit_future.result()
    youtube_videos = youtube_future.result()
    twitter_posts = twitter_future.result()
```

### 4.3 前端状态管理

使用 Provider 进行状态管理，避免不必要的重建：

```dart
class DataProvider with ChangeNotifier {
  DashboardData? _dashboardData;
  
  Future<void> refreshDashboard() async {
    _dashboardData = await _apiService.fetchDashboardData();
    notifyListeners();  // 通知所有监听者
  }
}
```

## 5. 安全考虑

### 5.1 API Key 保护

```python
# 使用环境变量
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

### 5.2 SQL 注入防护

```python
# 使用参数化查询
cursor.execute(
    "SELECT * FROM cleaned_data WHERE keyword = ?",
    (keyword,)
)
```

### 5.3 CORS 配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 6. 测试策略

### 6.1 单元测试

```python
def test_clean_text():
    text = "Hello &amp; World http://example.com"
    result = clean_text(text)
    assert result == "Hello World"
```

### 6.2 集成测试

```bash
python test_keyword_isolation.py
python test_report_isolation.py
python test_keyword_switch.py
```

### 6.3 端到端测试

```bash
python test_complete_flow.py
```

## 7. 部署建议

### 7.1 后端部署

```bash
# 使用 Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app

# 使用 Docker
docker build -t sentiment-api .
docker run -p 8888:8888 sentiment-api
```

### 7.2 前端部署

```bash
cd frontend
flutter build web
# 将 build/web 目录部署到静态服务器
```

### 7.3 数据库备份

```bash
# 定期备份
cp multi_source.db multi_source_backup_$(date +%Y%m%d).db
```

## 8. 监控与日志

### 8.1 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 8.2 性能监控

```python
import time

start_time = time.time()
# 执行操作
elapsed_time = time.time() - start_time
logger.info(f"操作耗时: {elapsed_time:.2f}秒")
```

## 9. 总结

本系统采用了多种技术和策略：

1. **数据采集**：多平台、多方案、容错机制
2. **AI 分析**：MapReduce 架构、Token 控制、Prompt 优化
3. **数据隔离**：按关键词和任务 ID 完全隔离
4. **前端展示**：Flutter Web、状态管理、主题切换
5. **问题解决**：数据隔离、报告隔离、页面刷新等

通过这些技术方案，实现了一个稳定、高效、易用的舆情分析系统。
