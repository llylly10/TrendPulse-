import requests
import sqlite3
import time
import html
import traceback
import re
import argparse
from bs4 import BeautifulSoup

# YouTube
from youtube_search import YoutubeSearch  # pip install youtube-search-python
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Twitter
# 注意: snscrape 因 Twitter (X) 政策变更目前已失效，暂注释掉
# import snscrape.modules.twitter as sntwitter

# Twitter Selenium 备选方案
try:
    from twitter_scraper_selenium import fetch_twitter_selenium
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium 爬虫未安装，将只使用 Nitter 镜像站")
from data_cleaning import process_data


DB_NAME = "multi_source.db"

# ----------------- 1. 初始化数据库 (优化连接管理) -----------------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()

        # 采集任务表
        cur.execute("""
        CREATE TABLE IF NOT EXISTS crawl_task (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT,
            keyword TEXT,
            language TEXT,
            limit_count INTEGER,
            created_at INTEGER
        )
        """)

        # Reddit 数据
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reddit_submission (
            post_id TEXT PRIMARY KEY,
            task_id INTEGER,
            title TEXT,
            subreddit TEXT,
            score INTEGER,
            num_comments INTEGER,
            created_utc INTEGER,
            is_self INTEGER,
            is_stickied INTEGER,
            url TEXT
        )
        """)

        # YouTube 数据
        cur.execute("""
        CREATE TABLE IF NOT EXISTS youtube_video (
            video_id TEXT PRIMARY KEY,
            task_id INTEGER,
            title TEXT,
            channel TEXT,
            published_at TEXT,
            view_count INTEGER,
            url TEXT,
            transcript TEXT
        )
        """)

        # Twitter 数据
        cur.execute("""
        CREATE TABLE IF NOT EXISTS twitter_tweet (
            tweet_id TEXT PRIMARY KEY,
            task_id INTEGER,
            content TEXT,
            username TEXT,
            created_at TEXT,
            retweet_count INTEGER,
            like_count INTEGER,
            url TEXT
        )
        """)
        conn.commit()

# ----------------- 2. 创建采集任务 -----------------
def create_task(source_type, keyword, language, limit_count):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO crawl_task (source_type, keyword, language, limit_count, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (source_type, keyword, language, limit_count, int(time.time())))
        task_id = cur.lastrowid
        conn.commit()
    return task_id

# ----------------- 3. Reddit (增强反爬伪装) -----------------
def fetch_reddit(keyword, limit=30, language="en"):
    # 伪装成真实浏览器 User-Agent，避免 429 错误
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = "https://www.reddit.com/search.json"
    params = {"q": keyword, "limit": limit, "sort": "new", "type": "link"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        
        if resp.status_code == 429:
            print("❌ Reddit 返回 429 (Too Many Requests). 建议使用官方 PRAW 库。")
            return []
        
        resp.raise_for_status()
        data = resp.json()
        posts = []

        for item in data.get("data", {}).get("children", []):
            p = item["data"]
            posts.append({
                "post_id": p["id"],
                "title": html.unescape(p.get("title", "")),
                "subreddit": p.get("subreddit"),
                "score": p.get("score"),
                "num_comments": p.get("num_comments"),
                "created_utc": p.get("created_utc"),
                "is_self": int(p.get("is_self", False)),
                "is_stickied": int(p.get("stickied", False)),
                "url": "https://www.reddit.com" + p.get("permalink", "")
            })
        return posts
    except requests.exceptions.Timeout:
        print("❌ Reddit 请求超时，跳过。")
        return []
    except Exception as e:
        print(f"❌ Reddit 抓取失败: {e}")
        return []

def save_reddit(task_id, posts):
    if not posts: return
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        for p in posts:
            cur.execute("""
            INSERT OR IGNORE INTO reddit_submission
            (post_id, task_id, title, subreddit, score, num_comments,
             created_utc, is_self, is_stickied, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["post_id"], task_id, p["title"], p["subreddit"],
                p["score"], p["num_comments"], p["created_utc"],
                p["is_self"], p["is_stickied"], p["url"]
            ))
        conn.commit()

# ----------------- 4. YouTube (处理数字转换) -----------------
def parse_view_count(view_text):
    """处理 '1.2M views', '500K views', 'No views' 等情况"""
    try:
        if not view_text: return 0
        text = view_text.replace("views", "").replace(",", "").strip()
        if "No" in text: return 0
        
        multiplier = 1
        if "K" in text:
            multiplier = 1000
            text = text.replace("K", "")
        elif "M" in text:
            multiplier = 1000000
            text = text.replace("M", "")
        elif "B" in text:
            multiplier = 1000000000
            text = text.replace("B", "")
            
        return int(float(text) * multiplier)
    except:
        return 0

def fetch_youtube(keyword, limit=10, language="en"):
    try:
        results = YoutubeSearch(keyword, max_results=limit).to_dict()
        videos = []
        for r in results:
            videos.append({
                "video_id": r["id"],
                "title": r["title"],
                "channel": r["channel"],
                "published_at": r.get("publish_time", ""),
                "view_count": parse_view_count(r.get("views", "0")), # 使用新解析函数
                "url": "https://www.youtube.com" + r["url_suffix"],
                "transcript": ""
            })
        return videos
    except requests.exceptions.Timeout:
        print("❌ YouTube 请求超时，跳过。")
        return []
    except Exception as e:
        print(f"❌ YouTube 搜索失败: {e}")
        return []

def fetch_transcripts(videos, lang='en'):
    for v in videos:
        try:
            transcript_obj = YouTubeTranscriptApi.list_transcripts(v["video_id"])
            # 优先找手动字幕，没有则找自动生成的
            try:
                t = transcript_obj.find_manually_created_transcript([lang])
            except:
                t = transcript_obj.find_generated_transcript([lang])
            
            transcript_list = t.fetch()
            v["transcript"] = " ".join([x["text"] for x in transcript_list])
            print(f"   ✅ 获取字幕成功: {v['title'][:20]}...")
        except (TranscriptsDisabled, NoTranscriptFound):
            print(f"   ⚠️ 无字幕: {v['title'][:20]}...")
            v["transcript"] = ""
        except Exception as e:
            # print(f"   ❌ 字幕获取出错 {v['video_id']}: {e}")
            v["transcript"] = ""
    return videos

def save_youtube(task_id, videos):
    if not videos: return
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        for v in videos:
            cur.execute("""
            INSERT OR IGNORE INTO youtube_video
            (video_id, task_id, title, channel, published_at, view_count, url, transcript)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                v["video_id"], task_id, v["title"], v["channel"],
                v["published_at"], v["view_count"], v["url"], v["transcript"]
            ))
        conn.commit()

# ----------------- 5. Twitter (使用 Nitter 镜像站) -----------------
def fetch_twitter(keyword, limit=30, language="en"):
    """使用 Nitter 镜像站抓取推文内容"""
    # 可用的 Nitter 实例列表
    instances = [
        "nitter.poast.org",
        "nitter.privacyredirect.com",
        "nitter.tiekoetter.com"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    tweets = []
    
    for instance in instances:
        if len(tweets) >= limit:
            break
            
        url = f"https://{instance}/search"
        params = {"q": keyword, "l": language}
        
        try:
            print(f"   🔍 尝试从 {instance} 抓取...")
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"   ⚠️ {instance} 返回状态码 {resp.status_code}")
                continue
                
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select(".timeline-item")
            
            for item in items:
                if len(tweets) >= limit:
                    break
                    
                # 排除非推文项（如"加载更多"）
                if "show-more" in item.get("class", []):
                    continue
                
                try:
                    # 提取推文 ID 和 URL
                    tweet_link_el = item.select_one(".tweet-link")
                    if not tweet_link_el:
                        continue
                    tweet_path = tweet_link_el.get("href")  # /username/status/123456#m
                    tweet_id = tweet_path.split("/")[-1].split("#")[0]
                    
                    # 提取内容
                    content_el = item.select_one(".tweet-content")
                    content = content_el.get_text(strip=True) if content_el else ""
                    
                    # 提取用户名
                    username_el = item.select_one(".username")
                    username = username_el.get_text(strip=True) if username_el else ""
                    
                    # 提取时间
                    date_el = item.select_one(".tweet-date a")
                    created_at = date_el.get("title") if date_el else ""
                    
                    # 提取统计数据
                    stats = item.select(".tweet-stats .icon-container")
                    retweet_count = 0
                    like_count = 0
                    for stat in stats:
                        text = stat.get_text(strip=True).replace(",", "")
                        if not text:
                            continue
                        
                        # 根据图标类名判断
                        icon = stat.select_one("span")
                        if not icon:
                            continue
                        icon_class = icon.get("class", [])
                        
                        if "icon-retweet" in icon_class:
                            retweet_count = int(text) if text.isdigit() else 0
                        elif "icon-heart" in icon_class:
                            like_count = int(text) if text.isdigit() else 0

                    tweets.append({
                        "tweet_id": tweet_id,
                        "content": content,
                        "username": username,
                        "created_at": created_at,
                        "retweet_count": retweet_count,
                        "like_count": like_count,
                        "url": f"https://twitter.com{tweet_path.split('#')[0]}"
                    })
                except Exception as e:
                    # print(f"   ❌ 解析单条推文失败: {e}")
                    continue
                    
            if tweets:
                print(f"   ✅ 从 {instance} 成功获取 {len(tweets)} 条推文")
                break  # 如果抓取到了，就暂时不尝试其他实例
                
        except requests.exceptions.Timeout:
            print(f"   ❌ 访问 {instance} 超时，跳过。")
            continue
        except Exception as e:
            print(f"   ❌ 访问 {instance} 出错: {e}")
            continue
            
    # 如果 Nitter 全部失败，尝试 Selenium 方案
    if not tweets and SELENIUM_AVAILABLE:
        print("   ⚠️ 所有 Nitter 实例均失败，切换到 Selenium 方案...")
        try:
            tweets = fetch_twitter_selenium(keyword, limit)
        except Exception as e:
            print(f"   ❌ Selenium 方案也失败了: {e}")
    elif not tweets and not SELENIUM_AVAILABLE:
        print("   ⚠️ Nitter 失败且 Selenium 未安装")
        print("   💡 运行: uv pip install selenium webdriver-manager")
            
    return tweets

def save_twitter(task_id, tweets):
    if not tweets:
        return
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        for t in tweets:
            cur.execute("""
            INSERT OR IGNORE INTO twitter_tweet
            (tweet_id, task_id, content, username, created_at, retweet_count, like_count, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t["tweet_id"], task_id, t["content"], t["username"],
                t["created_at"], t["retweet_count"], t["like_count"], t["url"]
            ))
        conn.commit()

# ----------------- 6. 统一采集入口 -----------------
def run_collection(keyword, language="en", reddit_limit=30, youtube_limit=30, twitter_limit=30):
    print("--- 正在初始化数据库 ---")
    init_db()

    # -------- Reddit ----------
    reddit_task_id = create_task("reddit", keyword, language, reddit_limit)
    print(f"\n[Reddit 任务 {reddit_task_id}] 正在抓取 '{keyword}'...")
    reddit_posts = fetch_reddit(keyword, reddit_limit, language)
    save_reddit(reddit_task_id, reddit_posts)
    print(f"成功保存 {len(reddit_posts)} 条 Reddit 帖子。")

    # -------- YouTube ----------
    youtube_task_id = create_task("youtube", keyword, language, youtube_limit)
    print(f"\n[YouTube 任务 {youtube_task_id}] 正在抓取 '{keyword}'...")
    youtube_videos = fetch_youtube(keyword, youtube_limit, language)
    if youtube_videos:
        # 获取字幕可能比较慢
        youtube_videos = fetch_transcripts(youtube_videos, language)
        save_youtube(youtube_task_id, youtube_videos)
    print(f"成功保存 {len(youtube_videos)} 个 YouTube 视频。")

    # -------- Twitter ----------
    twitter_task_id = create_task("twitter", keyword, language, twitter_limit)
    print(f"\n[Twitter 任务 {twitter_task_id}] 正在抓取 '{keyword}'...")
    twitter_posts = fetch_twitter(keyword, twitter_limit, language)
    save_twitter(twitter_task_id, twitter_posts)
    print(f"成功保存 {len(twitter_posts)} 条 Twitter 推文。")

    # -------- 自动清洗 ----------
    print("\n--- 所有采集任务已完成，开始自动清洗数据 ---")
    # 只清洗当前任务的数据
    task_ids = [reddit_task_id, youtube_task_id, twitter_task_id]
    process_data(keyword, task_ids)

# ----------------- 主程序 -----------------
def main():
    parser = argparse.ArgumentParser(description="多源舆情数据采集工具")
    parser.add_argument("--keyword", type=str, help="查询关键词")
    parser.add_argument("--language", type=str, choices=["en", "zh"], default="en", help="语言 (en/zh)")
    parser.add_argument("--reddit", type=int, default=30, help="Reddit 抓取限制")
    parser.add_argument("--youtube", type=int, default=30, help="YouTube 抓取限制")
    parser.add_argument("--twitter", type=int, default=30, help="Twitter 抓取限制")
    
    args = parser.parse_args()

    # 如果没有提供关键词，则进入交互模式（或者使用默认值）
    if not args.keyword:
        print("\n💡 未检测到命令行参数，进入默认配置模式...")
        keyword = "DeepSeek"
        language = "en"
        reddit_limit = 30
        youtube_limit = 30
        twitter_limit = 30
    else:
        keyword = args.keyword
        language = args.language
        reddit_limit = args.reddit
        youtube_limit = args.youtube
        twitter_limit = args.twitter
    
    run_collection(keyword, language, reddit_limit, youtube_limit, twitter_limit)

if __name__ == "__main__":
    main()