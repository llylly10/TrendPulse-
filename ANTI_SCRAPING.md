# 反爬虫策略文档

## 概述

本项目需要从 Reddit、YouTube、Twitter 三个平台采集公开数据。由于这些平台都有反爬虫机制，我们采用了多种策略来绕过限制。

## 1. Reddit 采集策略

### 1.1 使用官方 API

Reddit 提供了官方的 JSON API，无需认证即可访问公开数据。

```python
url = f"https://www.reddit.com/search.json"
params = {
    "q": keyword,
    "limit": limit,
    "sort": "relevance"
}
```

### 1.2 User-Agent 伪装

模拟真实浏览器访问：

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### 1.3 超时处理

设置合理的超时时间，避免长时间等待：

```python
response = requests.get(url, headers=headers, params=params, timeout=10)
```

### 1.4 异常处理

对各种异常情况进行处理：

```python
try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
except requests.exceptions.Timeout:
    print("❌ Reddit 请求超时")
except Exception as e:
    print(f"❌ Reddit 搜索失败: {e}")
```

## 2. YouTube 采集策略

### 2.1 使用第三方库

使用 `youtube-search-python` 库，避免直接解析 HTML：

```python
from youtube_search import YoutubeSearch

results = YoutubeSearch(keyword, max_results=limit).to_dict()
```

### 2.2 字幕获取

使用 `youtube-transcript-api` 获取视频字幕：

```python
from youtube_transcript_api import YouTubeTranscriptApi

transcript_obj = YouTubeTranscriptApi.list_transcripts(video_id)
# 优先获取手动字幕
try:
    t = transcript_obj.find_manually_created_transcript([lang])
except:
    t = transcript_obj.find_generated_transcript([lang])
```

### 2.3 异常处理

处理无字幕、字幕禁用等情况：

```python
try:
    transcript_list = t.fetch()
    transcript = " ".join([x["text"] for x in transcript_list])
except (TranscriptsDisabled, NoTranscriptFound):
    print(f"⚠️ 无字幕: {video_title}")
    transcript = ""
```

## 3. Twitter 采集策略

Twitter 的反爬虫最严格，我们采用了多层备选方案。

### 3.1 主要方案：Nitter 镜像站

Nitter 是 Twitter 的开源前端，提供无需认证的访问。

#### 镜像站轮询

维护多个 Nitter 实例，失败时自动切换：

```python
instances = [
    "nitter.poast.org",
    "nitter.privacyredirect.com",
    "nitter.tiekoetter.com"
]

for instance in instances:
    try:
        url = f"https://{instance}/search"
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            # 解析数据
            break
    except:
        continue  # 尝试下一个实例
```

#### User-Agent 伪装

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
```

#### HTML 解析

使用 BeautifulSoup 解析 Nitter 返回的 HTML：

```python
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
    stats = item.select(".tweet-stats .icon-container")
```

### 3.2 备选方案：Selenium

如果所有 Nitter 实例都失败，使用 Selenium 模拟浏览器：

```python
if not tweets and SELENIUM_AVAILABLE:
    print("⚠️ 所有 Nitter 实例均失败，切换到 Selenium 方案...")
    try:
        from twitter_scraper_selenium import fetch_twitter_selenium
        tweets = fetch_twitter_selenium(keyword, limit)
    except Exception as e:
        print(f"❌ Selenium 方案也失败: {e}")
```

#### Selenium 优势

- 完全模拟真实浏览器行为
- 可以执行 JavaScript
- 可以处理动态加载的内容

#### Selenium 劣势

- 速度慢
- 资源消耗大
- 需要安装浏览器驱动

## 4. 通用反爬策略

### 4.1 请求频率控制

避免短时间内发送大量请求：

```python
import time

# 在请求之间添加延迟
time.sleep(1)  # 延迟 1 秒
```

### 4.2 异常重试机制

对失败的请求进行重试：

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            break
    except:
        if attempt < max_retries - 1:
            time.sleep(2)  # 等待后重试
            continue
        else:
            raise
```

### 4.3 数据去重

使用唯一 ID 去重，避免重复采集：

```python
# 使用 INSERT OR IGNORE 避免重复
cursor.execute("""
    INSERT OR IGNORE INTO reddit_submission (post_id, ...)
    VALUES (?, ...)
""", (post_id, ...))
```

### 4.4 错误日志

记录所有错误，便于调试：

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # 采集逻辑
except Exception as e:
    logger.error(f"采集失败: {e}")
```

## 5. 数据清洗

### 5.1 HTML 实体解码

```python
import html

text = html.unescape(text)  # &amp; -> &
```

### 5.2 URL 移除

```python
import re

text = re.sub(r'http[s]?://\S+', '', text)
```

### 5.3 特殊字符过滤

```python
# 保留中文、英文、数字和基本标点
text = re.sub(r'[^\w\s\u4e00-\u9fa5,.!?，。！？]', '', text)
```

### 5.4 空白字符规范化

```python
text = re.sub(r'\s+', ' ', text).strip()
```

## 6. 法律与道德考虑

### 6.1 遵守 robots.txt

检查目标网站的 robots.txt 文件，遵守爬虫规则。

### 6.2 仅采集公开数据

只采集公开可见的数据，不尝试访问需要登录的内容。

### 6.3 合理使用频率

控制请求频率，避免对目标服务器造成负担。

### 6.4 尊重版权

采集的数据仅用于分析，不进行商业用途。

## 7. 未来改进方向

### 7.1 IP 代理池

使用代理 IP 轮换，避免单个 IP 被封禁：

```python
proxies = {
    'http': 'http://proxy1.com:8080',
    'https': 'https://proxy1.com:8080',
}
response = requests.get(url, proxies=proxies)
```

### 7.2 分布式采集

使用 Celery 等任务队列，实现分布式采集：

```python
from celery import Celery

@celery.task
def fetch_data(keyword):
    # 采集逻辑
    pass
```

### 7.3 验证码识别

使用 OCR 或第三方服务识别验证码：

```python
from PIL import Image
import pytesseract

captcha_text = pytesseract.image_to_string(Image.open('captcha.png'))
```

### 7.4 Cookie 管理

维护 Session，保持登录状态：

```python
session = requests.Session()
session.cookies.set('cookie_name', 'cookie_value')
response = session.get(url)
```

## 8. 总结

本项目采用了多层次的反爬策略：

1. **优先使用官方 API**（Reddit）
2. **使用第三方库**（YouTube）
3. **镜像站轮询**（Twitter Nitter）
4. **Selenium 备选**（Twitter）
5. **通用策略**（User-Agent、超时、重试、去重）

这些策略确保了数据采集的稳定性和可靠性，同时遵守了法律和道德规范。
