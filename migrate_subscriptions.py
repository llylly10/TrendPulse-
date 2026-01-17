"""迁移订阅表：interval_hours -> interval_seconds"""
import sqlite3

conn = sqlite3.connect("multi_source.db")
cursor = conn.cursor()

try:
    # 检查是否已经有 interval_seconds 列
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'interval_seconds' in columns:
        print("✓ 数据库已经是最新版本")
    elif 'interval_hours' in columns:
        print("🔄 开始迁移数据库...")
        
        # 创建新表
        cursor.execute("""
            CREATE TABLE subscriptions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                reddit_limit INTEGER DEFAULT 30,
                youtube_limit INTEGER DEFAULT 30,
                twitter_limit INTEGER DEFAULT 30,
                interval_seconds INTEGER DEFAULT 21600,
                last_run INTEGER DEFAULT 0,
                next_run INTEGER DEFAULT 0
            )
        """)
        
        # 复制数据，将 interval_hours 转换为 interval_seconds
        cursor.execute("""
            INSERT INTO subscriptions_new 
            (id, keyword, language, reddit_limit, youtube_limit, twitter_limit, interval_seconds, last_run, next_run)
            SELECT 
                id, keyword, language, reddit_limit, youtube_limit, twitter_limit, 
                interval_hours * 3600, last_run, next_run
            FROM subscriptions
        """)
        
        # 删除旧表
        cursor.execute("DROP TABLE subscriptions")
        
        # 重命名新表
        cursor.execute("ALTER TABLE subscriptions_new RENAME TO subscriptions")
        
        conn.commit()
        print("✓ 迁移完成！")
        print("  - interval_hours 已转换为 interval_seconds")
    else:
        print("⚠️ 表结构不符合预期，请检查数据库")
        
except Exception as e:
    print(f"✗ 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()
