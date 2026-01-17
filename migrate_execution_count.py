#!/usr/bin/env python3
"""
迁移脚本：为 subscriptions 表添加 execution_count 列
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "multi_source.db"

def migrate():
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        
        # 检查列是否已存在
        cur.execute("PRAGMA table_info(subscriptions)")
        columns = [row[1] for row in cur.fetchall()]
        
        if "execution_count" not in columns:
            logger.info("添加 execution_count 列...")
            cur.execute("ALTER TABLE subscriptions ADD COLUMN execution_count INTEGER DEFAULT 0")
            conn.commit()
            logger.info("✓ 迁移完成")
        else:
            logger.info("execution_count 列已存在，无需迁移")
        
        conn.close()
    except Exception as e:
        logger.error(f"迁移失败: {e}")

if __name__ == "__main__":
    migrate()
