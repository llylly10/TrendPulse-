import sqlite3
import re
import html
import json
from datetime import datetime
import pandas as pd

DB_NAME = "multi_source.db"

def clean_text(text):
    if not text:
        return ""
    
    # 1. 解码 HTML 实体 (如 &amp; -> &)
    text = html.unescape(text)
    
    # 2. 去除 URL 链接
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # 3. 保留中文字符、英文字符、数字和基本标点，去除其他杂质
    # \u4e00-\u9fa5 是中文范围
    text = re.sub(r'[^\w\s\u4e00-\u9fa5,.!?，。！？]', '', text)
    
    # 4. 规范化空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def normalize_time(val):
    """将各种时间格式统一为 ISO-8601 字符串"""
    if not val:
        return None
    
    try:
        # 如果是 Reddit 的 Unix 时间戳 (int/float)
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val).isoformat()
        
        # 如果是字符串格式
        val_str = str(val).strip()
        
        # 尝试解析常见的 ISO 格式或 Twitter/YouTube 格式
        # pandas 的 to_datetime 非常强大，可以处理大多数情况
        dt = pd.to_datetime(val_str, errors='coerce')
        if pd.notnull(dt):
            return dt.isoformat()
            
    except Exception as e:
        print(f"⚠️ 时间转换失败: {val} -> {e}")
    
    return str(val)

def process_data(keyword="unknown", task_ids=None):
    print(f"🚀 开始数据清洗流程 (关键词: {keyword})...")
    
    conn = sqlite3.connect(DB_NAME)
    
    # 如果指定了 task_ids，只处理这些任务的数据
    if task_ids:
        task_filter = f"WHERE task_id IN ({','.join(map(str, task_ids))})"
    else:
        task_filter = ""
    
    # 1. 读取 Reddit 数据
    print("📥 读取 Reddit 数据...")
    reddit_query = f"SELECT post_id, title, subreddit, score, created_utc, url FROM reddit_submission {task_filter}"
    reddit_df = pd.read_sql_query(reddit_query, conn)
    reddit_df = reddit_df.rename(columns={
        'post_id': 'raw_id',
        'title': 'content',
        'subreddit': 'author',
        'created_utc': 'raw_time'
    })
    reddit_df['platform'] = 'reddit'
    reddit_df['engagement'] = reddit_df['score'].apply(lambda x: json.dumps({'score': x}))

    # 2. 读取 YouTube 数据
    print("📥 读取 YouTube 数据...")
    youtube_query = f"SELECT video_id, title, channel, published_at, view_count, url FROM youtube_video {task_filter}"
    youtube_df = pd.read_sql_query(youtube_query, conn)
    youtube_df = youtube_df.rename(columns={
        'video_id': 'raw_id',
        'title': 'content',
        'channel': 'author',
        'published_at': 'raw_time'
    })
    youtube_df['platform'] = 'youtube'
    youtube_df['engagement'] = youtube_df['view_count'].apply(lambda x: json.dumps({'view_count': x}))

    # 3. 读取 Twitter 数据
    print("📥 读取 Twitter 数据...")
    twitter_query = f"SELECT tweet_id, content, username, created_at, retweet_count, like_count, url FROM twitter_tweet {task_filter}"
    twitter_df = pd.read_sql_query(twitter_query, conn)
    twitter_df = twitter_df.rename(columns={
        'tweet_id': 'raw_id',
        'username': 'author',
        'created_at': 'raw_time'
    })
    twitter_df['platform'] = 'twitter'
    twitter_df['engagement'] = twitter_df.apply(lambda r: json.dumps({'retweet_count': r['retweet_count'], 'like_count': r['like_count']}), axis=1)

    # 合并所有数据
    print("🔄 合并数据并进行清洗...")
    all_data = pd.concat([reddit_df, youtube_df, twitter_df], ignore_index=True)
    
    if all_data.empty:
        print("⚠️ 没有数据需要清洗")
        conn.close()
        return

    # 执行清洗逻辑
    all_data['content'] = all_data['content'].apply(clean_text)
    all_data['timestamp'] = all_data['raw_time'].apply(normalize_time)
    
    # 去重
    initial_count = len(all_data)
    all_data = all_data.drop_duplicates(subset=['platform', 'raw_id'])
    print(f"🧹 去重完成: {initial_count} -> {len(all_data)}")

    # 准备存入数据库的最终字段
    final_df = all_data[['platform', 'raw_id', 'content', 'author', 'timestamp', 'engagement', 'url']]
    
    # 添加关键词字段
    final_df['keyword'] = keyword

    # 存入数据库
    print(f"💾 正在将清洗后的数据存入 'cleaned_data' 表 (关键词: {keyword})...")
    final_df.to_sql('cleaned_data', conn, if_exists='append', index=False)
    
    conn.close()
    print("✅ 数据清洗完成！")

if __name__ == "__main__":
    import sys
    keyword = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    process_data(keyword)
