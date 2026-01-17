"""
Twitter 爬虫 - 使用 Selenium 无头浏览器方案
当 Nitter 镜像站不可用时的备选方案

依赖安装:
pip install selenium webdriver-manager
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import sqlite3
from datetime import datetime

DB_NAME = "multi_source.db"

def fetch_twitter_selenium(keyword, limit=30):
    """使用 Selenium 从 Nitter 或 xcancel 抓取推文"""
    
    # 配置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Nitter 实例列表
    nitter_instances = [
        "nitter.poast.org",
        "nitter.privacyredirect.com",
        "nitter.net",
        "nitter.unixfox.eu"
    ]
    
    tweets = []
    driver = None
    
    try:
        # 初始化 WebDriver
        print("   🚀 启动 Selenium WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        for instance in nitter_instances:
            if len(tweets) >= limit:
                break
            
            url = f"https://{instance}/search?q={keyword}&f=tweets"
            
            try:
                print(f"   🔍 尝试访问 {instance}...")
                driver.get(url)
                
                # 等待页面加载
                time.sleep(3)
                
                # 等待推文容器出现
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".timeline-item"))
                    )
                except:
                    print(f"   ⚠️ {instance} 加载超时或无推文")
                    continue
                
                # 滚动页面加载更多推文
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                
                # 查找所有推文元素
                tweet_elements = driver.find_elements(By.CSS_SELECTOR, ".timeline-item")
                print(f"   📝 找到 {len(tweet_elements)} 个时间线项目")
                
                for tweet_elem in tweet_elements:
                    if len(tweets) >= limit:
                        break
                    
                    try:
                        # 检查是否为有效推文
                        if "show-more" in tweet_elem.get_attribute("class"):
                            continue
                        
                        # 提取推文链接和 ID
                        try:
                            link_elem = tweet_elem.find_element(By.CSS_SELECTOR, ".tweet-link")
                        except:
                            try:
                                link_elem = tweet_elem.find_element(By.CSS_SELECTOR, ".tweet-date a")
                            except:
                                continue
                        
                        tweet_path = link_elem.get_attribute("href")
                        if not tweet_path or "/status/" not in tweet_path:
                            continue
                        
                        # 提取 tweet ID
                        parts = tweet_path.split("/")
                        try:
                            status_idx = parts.index("status")
                            tweet_id = parts[status_idx + 1].split("#")[0].split("?")[0]
                        except:
                            continue
                        
                        # 提取用户名
                        try:
                            username_elem = tweet_elem.find_element(By.CSS_SELECTOR, ".username")
                            username = username_elem.text.strip().lstrip("@")
                        except:
                            username = ""
                        
                        # 提取推文内容
                        try:
                            content_elem = tweet_elem.find_element(By.CSS_SELECTOR, ".tweet-content")
                            content = content_elem.text.strip()
                        except:
                            content = ""
                        
                        if not content:
                            continue
                        
                        # 提取时间
                        try:
                            date_elem = tweet_elem.find_element(By.CSS_SELECTOR, ".tweet-date a")
                            created_at = date_elem.get_attribute("title")
                            if not created_at:
                                created_at = date_elem.text.strip()
                        except:
                            created_at = ""
                        
                        # 提取统计数据
                        retweet_count = 0
                        like_count = 0
                        
                        try:
                            stat_elems = tweet_elem.find_elements(By.CSS_SELECTOR, ".tweet-stats .icon-container")
                            for stat_elem in stat_elems:
                                text = stat_elem.text.strip().replace(",", "")
                                if not text.isdigit():
                                    continue
                                
                                # 检查图标类型
                                try:
                                    icon = stat_elem.find_element(By.CSS_SELECTOR, "span")
                                    icon_class = icon.get_attribute("class")
                                    
                                    if "icon-retweet" in icon_class:
                                        retweet_count = int(text)
                                    elif "icon-heart" in icon_class:
                                        like_count = int(text)
                                except:
                                    pass
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
                        # print(f"   ❌ 解析单条推文失败: {e}")
                        continue
                
                if tweets:
                    print(f"   ✅ 从 {instance} 成功获取 {len(tweets)} 条推文")
                    break
                else:
                    print(f"   ⚠️ {instance} 未能解析出有效推文")
                    
            except Exception as e:
                print(f"   ❌ 访问 {instance} 出错: {e}")
                continue
    
    except Exception as e:
        print(f"   ❌ Selenium 初始化失败: {e}")
    
    finally:
        if driver:
            driver.quit()
            print("   🔚 关闭 WebDriver")
    
    return tweets

def save_twitter_selenium(task_id, tweets):
    """保存推文到数据库"""
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

if __name__ == "__main__":
    # 测试
    print("开始测试 Selenium Twitter 爬虫...")
    tweets = fetch_twitter_selenium("DeepSeek", limit=10)
    print(f"\n总共获取 {len(tweets)} 条推文")
    
    if tweets:
        print("\n前 3 条推文预览:")
        for i, tweet in enumerate(tweets[:3], 1):
            print(f"\n{i}. @{tweet['username']}")
            print(f"   内容: {tweet['content'][:100]}...")
            print(f"   时间: {tweet['created_at']}")
            print(f"   互动: ❤️ {tweet['like_count']} | 🔁 {tweet['retweet_count']}")
