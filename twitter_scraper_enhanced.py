"""
增强版 Twitter 爬虫函数
可以直接替换 collect.py 中的 fetch_twitter 函数使用

改进点:
1. 更多 Nitter 实例
2. 更健壮的 HTML 解析
3. 更好的错误处理
4. 支持多种 HTML 结构
"""

import requests
from bs4 import BeautifulSoup
import time

def fetch_twitter_enhanced(keyword, limit=30):
    """增强版 Nitter 爬虫 - 更健壮的实现"""
    
    # 更全面的 Nitter 实例列表（定期更新）
    instances = [
        "nitter.poast.org",
        "nitter.privacyredirect.com", 
        "nitter.tiekoetter.com",
        "nitter.net",
        "nitter.unixfox.eu",
        "nitter.kavin.rocks",
        "nitter.fdn.fr",
        "nitter.1d4.us",
        "nitter.hu",
        "nitter.cz"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    tweets = []
    successful_instance = None
    
    for instance in instances:
        if len(tweets) >= limit:
            break
            
        url = f"https://{instance}/search"
        params = {"q": keyword, "f": "tweets"}  # f=tweets 只显示推文
        
        try:
            print(f"   🔍 尝试从 {instance} 抓取...")
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            
            if resp.status_code != 200:
                print(f"   ⚠️ {instance} 返回状态码 {resp.status_code}")
                continue
                
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # 尝试多种可能的选择器（不同的 Nitter 实例可能 HTML 结构略有不同）
            items = soup.select(".timeline-item")
            if not items:
                items = soup.select("div.timeline-item")
            if not items:
                print(f"   ⚠️ {instance} 未找到推文容器")
                continue
            
            print(f"   📝 找到 {len(items)} 个时间线项目")
            
            for item in items:
                if len(tweets) >= limit:
                    break
                    
                # 排除非推文项（如"加载更多"）
                item_classes = item.get("class", [])
                if "show-more" in item_classes or "timeline-protected" in item_classes:
                    continue
                
                try:
                    # 方法1: 通过 .tweet-link 获取链接
                    tweet_link_el = item.select_one(".tweet-link")
                    if not tweet_link_el:
                        # 方法2: 通过 .tweet-date a 获取链接
                        tweet_link_el = item.select_one(".tweet-date a")
                    
                    if not tweet_link_el:
                        continue
                    
                    tweet_path = tweet_link_el.get("href", "")
                    if not tweet_path or "/status/" not in tweet_path:
                        continue
                    
                    # 提取推文 ID（更健壮的方式）
                    try:
                        # tweet_path 格式: /username/status/123456789#m
                        parts = tweet_path.split("/")
                        status_index = parts.index("status") if "status" in parts else -1
                        if status_index > 0 and status_index + 1 < len(parts):
                            tweet_id = parts[status_index + 1].split("#")[0].split("?")[0]
                            username_from_path = parts[status_index - 1] if status_index > 0 else ""
                        else:
                            continue
                    except:
                        continue
                    
                    # 提取用户名（多种方式）
                    username_el = item.select_one(".username")
                    if not username_el:
                        username_el = item.select_one(".fullname + a")
                    username = username_el.get_text(strip=True).lstrip("@") if username_el else username_from_path
                    
                    # 提取推文内容
                    content_el = item.select_one(".tweet-content")
                    if not content_el:
                        content_el = item.select_one("div.tweet-content")
                    content = content_el.get_text(separator=" ", strip=True) if content_el else ""
                    
                    # 如果内容为空,跳过
                    if not content:
                        continue
                    
                    # 提取时间
                    date_el = item.select_one(".tweet-date a")
                    created_at = ""
                    if date_el:
                        created_at = date_el.get("title", "")
                        if not created_at:
                            created_at = date_el.get_text(strip=True)
                    
                    # 提取统计数据（更健壮的解析）
                    retweet_count = 0
                    like_count = 0
                    
                    # 尝试从 .tweet-stats 提取
                    stats_container = item.select_one(".tweet-stats")
                    if stats_container:
                        # 查找转发数
                        retweet_el = stats_container.select_one(".icon-retweet")
                        if retweet_el:
                            parent = retweet_el.find_parent("div", class_="icon-container")
                            if parent:
                                text = parent.get_text(strip=True).replace(",", "")
                                try:
                                    retweet_count = int(text) if text.isdigit() else 0
                                except:
                                    pass
                        
                        # 查找点赞数
                        like_el = stats_container.select_one(".icon-heart")
                        if like_el:
                            parent = like_el.find_parent("div", class_="icon-container")
                            if parent:
                                text = parent.get_text(strip=True).replace(",", "")
                                try:
                                    like_count = int(text) if text.isdigit() else 0
                                except:
                                    pass
                    
                    # 避免重复
                    if any(t["tweet_id"] == tweet_id for t in tweets):
                        continue
                    
                    tweets.append({
                        "tweet_id": tweet_id,
                        "content": content,
                        "username": username,
                        "created_at": created_at,
                        "retweet_count": retweet_count,
                        "like_count": like_count,
                        "url": f"https://twitter.com/{username}/status/{tweet_id}"
                    })
                    
                except Exception as e:
                    # 调试时可以取消注释查看具体错误
                    # print(f"   ❌ 解析单条推文失败: {e}")
                    # import traceback; traceback.print_exc()
                    continue
                    
            if tweets:
                successful_instance = instance
                print(f"   ✅ 从 {instance} 成功获取 {len(tweets)} 条推文")
                break  # 如果抓取到了，就暂时不尝试其他实例
            else:
                print(f"   ⚠️ {instance} 未能解析出有效推文")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ {instance} 请求超时")
            continue
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {instance} 连接失败")
            continue
        except Exception as e:
            print(f"   ❌ 访问 {instance} 出错: {e}")
            continue
    
    if not tweets:
        print(f"   ⚠️  所有 Nitter 实例均失败")
        print(f"   💡 建议方案:")
        print(f"      1. 检查网络连接")
        print(f"      2. 访问 https://github.com/zedeus/nitter/wiki/Instances 获取最新实例列表")
        print(f"      3. 使用 twitter_scraper_selenium.py (无头浏览器方案)")
        print(f"      4. 考虑使用付费 Twitter API")
    
    return tweets


# 测试代码
if __name__ == "__main__":
    print("测试增强版 Twitter 爬虫...")
    tweets = fetch_twitter_enhanced("DeepSeek", limit=10)
    
    print(f"\n总共获取 {len(tweets)} 条推文\n")
    
    if tweets:
        print("前 5 条推文预览:")
        print("=" * 80)
        for i, tweet in enumerate(tweets[:5], 1):
            print(f"\n{i}. @{tweet['username']}")
            print(f"   内容: {tweet['content'][:150]}...")
            print(f"   时间: {tweet['created_at']}")
            print(f"   互动: ❤️ {tweet['like_count']} | 🔁 {tweet['retweet_count']}")
            print(f"   链接: {tweet['url']}")
        print("\n" + "=" * 80)
    else:
        print("❌ 未能获取任何推文，请尝试 Selenium 方案")
