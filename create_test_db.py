"""创建测试数据库数据"""
import sqlite3

conn = sqlite3.connect("multi_source.db")
cursor = conn.cursor()

# 插入一些测试数据到 cleaned_data 表
test_posts = [
    ("reddit", "post1", "DeepSeek breakthrough in AI - Amazing progress!", "user1", "2024-01-15", "100", "http://reddit.com/1"),
    ("youtube", "video1", "DeepSeek review - Great model but privacy concerns", "user2", "2024-01-15", "200", "http://youtube.com/1"),
    ("twitter", "tweet1", "DeepSeek launch - Impressive cost reduction", "user3", "2024-01-15", "150", "http://twitter.com/1"),
]

for platform, raw_id, content, author, timestamp, engagement, url in test_posts:
    cursor.execute("""
        INSERT INTO cleaned_data (platform, raw_id, content, author, timestamp, engagement, url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (platform, raw_id, content, author, timestamp, engagement, url))

conn.commit()
conn.close()

print("✓ 测试数据已添加到数据库")
print(f"  - 添加了 {len(test_posts)} 条帖子")

