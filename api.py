from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import json
import os
import logging
import time
import threading
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Public Opinion Analysis API")

# 允许跨域 (Flutter Web 或其他前端需要)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "multi_source.db"
REPORT_FILE = "analysis_report.json"

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.start()

# 任务状态跟踪
task_status = {
    "is_running": False,
    "current_task": None,
    "last_update": 0,
    "progress": "",
}

def get_db_connection():
    if not os.path.exists(DB_NAME):
        # 如果数据库不存在，尝试初始化
        try:
            init_db_tables()
        except:
            logger.error(f"Database file {DB_NAME} not found and init failed.")
            return None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def init_db_tables():
    """初始化数据库表，包括新的订阅和报警表"""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        # 确保原有表存在 (简略)
        
        # 订阅表
        cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            reddit_limit INTEGER DEFAULT 30,
            youtube_limit INTEGER DEFAULT 30,
            twitter_limit INTEGER DEFAULT 30,
            interval_seconds INTEGER DEFAULT 21600,
            last_run INTEGER DEFAULT 0,
            next_run INTEGER DEFAULT 0,
            execution_count INTEGER DEFAULT 0
        )
        """)
        
        # 报警表
        cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER,
            message TEXT,
            created_at INTEGER,
            is_read INTEGER DEFAULT 0
        )
        """)
        conn.commit()

# 确保启动时检查表结构
try:
    init_db_tables()
except Exception as e:
    logger.warning(f"DB Init warning: {e}")

def clean_nan(obj):
    """递归清理字典或列表中的 NaN/Inf 值"""
    import math
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return obj
    return obj

# --- 调度任务逻辑 ---
def scheduled_collection_task(sub_id):
    global task_status
    logger.info(f"Running scheduled task for subscription {sub_id}")
    
    task_status["is_running"] = True
    task_status["current_task"] = f"subscription_{sub_id}"
    task_status["last_update"] = int(time.time())
    task_status["progress"] = "开始执行定时任务..."
    
    conn = get_db_connection()
    if not conn: 
        task_status["is_running"] = False
        return
    
    try:
        sub = conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
        if not sub: 
            task_status["is_running"] = False
            return
        
        keyword = sub["keyword"]
        language = sub["language"]
        
        # 1. 运行采集和分析
        from collect import run_collection
        from ai_analysis import run_analysis
        
        task_status["progress"] = f"正在采集数据: {keyword}"
        logger.info(f"Scheduled Collection: {keyword}")
        run_collection(keyword, language, sub["reddit_limit"], sub["youtube_limit"], sub["twitter_limit"])
        
        task_status["progress"] = "正在进行 AI 分析..."
        logger.info("Scheduled Analysis")
        run_analysis(language=language, keyword=keyword)
        
        # 2. 检查情感得分并报警
        task_status["progress"] = "检查情感得分..."
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, "r", encoding="utf-8") as f:
                report = json.load(f)
                score = report.get("avg_sentiment", 50)
                if score < 30:
                    msg = f"⚠️ 负面舆情报警: '{keyword}' 情感得分仅 {score:.1f}！"
                    conn.execute("INSERT INTO alerts (subscription_id, message, created_at) VALUES (?, ?, ?)",
                                 (sub_id, msg, int(time.time())))
                    conn.commit()
                    logger.warning(msg)
        
        # 3. 更新下次运行时间和执行计数
        now = int(time.time())
        next_run = now + sub["interval_seconds"]
        execution_count = (sub["execution_count"] or 0) + 1
        conn.execute("UPDATE subscriptions SET last_run = ?, next_run = ?, execution_count = ? WHERE id = ?",
                     (now, next_run, execution_count, sub_id))
        conn.commit()
        
        task_status["progress"] = "任务完成！"
        logger.info(f"✓ 定时任务完成: {keyword}")
        
    except Exception as e:
        logger.error(f"Scheduled task failed: {e}")
        task_status["progress"] = f"任务失败: {str(e)}"
    finally:
        conn.close()
        task_status["is_running"] = False
        task_status["last_update"] = int(time.time())

def check_subscriptions():
    """每分钟检查一次是否有任务需要运行"""
    logger.info("🔍 检查定时任务...")
    conn = get_db_connection()
    if not conn: 
        logger.error("数据库连接失败")
        return
    
    try:
        now = int(time.time())
        # 查找 next_run <= now 的任务
        subs = conn.execute("SELECT * FROM subscriptions WHERE next_run <= ?", (now,)).fetchall()
        
        logger.info(f"找到 {len(subs)} 个待执行任务")
        
        for sub in subs:
            logger.info(f"检查订阅 #{sub['id']}: {sub['keyword']}, next_run={sub['next_run']}, now={now}")
            
            # 简单的防重入：如果 last_run 很近（比如1分钟内），跳过
            if sub["last_run"] > 0 and now - sub["last_run"] < 60:
                logger.info(f"  跳过（最近刚执行过）")
                continue
            
            logger.info(f"  ✓ 触发任务执行: {sub['keyword']}")
            
            # 直接在后台线程中执行任务（不使用 scheduler）
            # 这样可以立即更新 task_status，前端可以立即看到进度
            import threading
            thread = threading.Thread(target=scheduled_collection_task, args=(sub["id"],), daemon=True)
            thread.start()
            
            # 更新 next_run 避免重复提交
            next_run_temp = now + sub["interval_seconds"]
            conn.execute("UPDATE subscriptions SET next_run = ? WHERE id = ?", (next_run_temp, sub["id"]))
            conn.commit()
            logger.info(f"  下次运行时间已更新: {next_run_temp}")
            
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
    finally:
        conn.close()

# 添加定时检查器
scheduler.add_job(check_subscriptions, 'interval', minutes=1)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Public Opinion Analysis API is running"}

@app.get("/api/dashboard")
async def get_dashboard(keyword: str = None):
    # 1. 检查数据库是否有数据
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        # 如果没有指定关键词，获取最新的关键词
        if not keyword:
            cursor.execute("SELECT keyword FROM cleaned_data WHERE keyword != 'unknown' ORDER BY rowid DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                keyword = result["keyword"]
                logger.info(f"Dashboard: 使用最新关键词 '{keyword}'")
        
        # 查询指定关键词的数据量
        if keyword:
            cursor.execute("SELECT COUNT(*) as total FROM cleaned_data WHERE keyword = ?", (keyword,))
        else:
            cursor.execute("SELECT COUNT(*) as total FROM cleaned_data")
        
        total_count = cursor.fetchone()["total"]
        
        # 如果没有数据，返回空状态
        if total_count == 0:
            conn.close()
            return {
                "heat_index": 0.0,
                "total_posts": 0,
                "sentiment": {
                    "score": 50.0,
                    "label": "暂无数据"
                },
                "key_points": [],
                "summary": "",
                "mermaid_graph": "",
                "node_sentiments": {},
                "keyword": keyword or ""
            }
        
        # 2. 读取 AI 分析报告 - 按关键词读取对应的报告文件
        report = {}
        if keyword:
            report_file = f"analysis_report_{keyword}.json"
        else:
            report_file = REPORT_FILE
        
        if os.path.exists(report_file):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)
                logger.info(f"Dashboard: 读取报告文件 {report_file}")
            except Exception as e:
                logger.error(f"Error reading report file {report_file}: {e}")
        else:
            logger.warning(f"Dashboard: 报告文件 {report_file} 不存在")
        
        # 如果报告为空，返回基础数据
        if not report:
            conn.close()
            return {
                "heat_index": 0.0,
                "total_posts": total_count,
                "sentiment": {
                    "score": 50.0,
                    "label": "分析中"
                },
                "key_points": [],
                "summary": "数据分析中，请稍后...",
                "mermaid_graph": ""
            }
        
        # 获取互动数 (解析 engagement JSON)
        if keyword:
            cursor.execute("SELECT engagement FROM cleaned_data WHERE keyword = ?", (keyword,))
        else:
            cursor.execute("SELECT engagement FROM cleaned_data")
        rows = cursor.fetchall()
        total_engagement = 0
        import math
        def safe_add(current, val):
            try:
                v = float(val) if val is not None else 0
                if math.isnan(v) or math.isinf(v):
                    return current
                return current + v
            except:
                return current

        for row in rows:
            try:
                eng_str = row["engagement"]
                if eng_str:
                    eng = json.loads(eng_str)
                    total_engagement = safe_add(total_engagement, eng.get("score"))
                    total_engagement = safe_add(total_engagement, eng.get("view_count"))
                    total_engagement = safe_add(total_engagement, eng.get("retweet_count"))
                    total_engagement = safe_add(total_engagement, eng.get("like_count"))
                    total_engagement = safe_add(total_engagement, eng.get("num_comments"))
            except Exception as e:
                logger.warning(f"Error parsing engagement JSON: {e}")
                continue
        
        conn.close()
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail="Database query failed")
    
    # 计算热度指标 (简单加权)
    heat_index = total_count + (total_engagement / 10.0 if total_engagement else 0)
    
    # 确保 heat_index 不是 NaN
    if math.isnan(heat_index) or math.isinf(heat_index):
        heat_index = 0
    
    return clean_nan({
        "heat_index": float(heat_index),
        "total_posts": int(total_count),
        "sentiment": {
            "score": float(report.get("avg_sentiment", 50)),
            "label": "正面" if report.get("avg_sentiment", 50) > 60 else ("负面" if report.get("avg_sentiment", 50) < 40 else "中性")
        },
        "key_points": report.get("final_controversies", []),
        "summary": report.get("human_summary", "暂无摘要"),
        "mermaid_graph": report.get("mermaid_graph", ""),
        "node_sentiments": report.get("node_sentiments", {}),
        "keyword": keyword or ""
    })

@app.get("/api/source-data")
async def get_source_data(keyword: str = None):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cleaned_data'")
        if not cursor.fetchone():
            conn.close()
            return []
        
        # 如果没有指定关键词，获取最新的关键词
        if not keyword:
            cursor.execute("SELECT keyword FROM cleaned_data WHERE keyword != 'unknown' ORDER BY rowid DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                keyword = result["keyword"]
        
        # 按关键词查询
        if keyword:
            cursor.execute("SELECT platform, content, author, timestamp, engagement, url, keyword FROM cleaned_data WHERE keyword = ? ORDER BY timestamp DESC", (keyword,))
        else:
            cursor.execute("SELECT platform, content, author, timestamp, engagement, url, keyword FROM cleaned_data ORDER BY timestamp DESC")
        
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            item = dict(row)
            try:
                if item["engagement"]:
                    item["engagement"] = json.loads(item["engagement"])
                else:
                    item["engagement"] = {}
            except:
                item["engagement"] = {}
            result.append(item)
        
        conn.close()
        return clean_nan(result)
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        if conn:
            conn.close()
        return []

@app.post("/api/collect")
async def collect_data(params: dict, background_tasks: BackgroundTasks):
    global task_status
    
    keyword = params.get("keyword", "DeepSeek")
    language = params.get("language", "en")
    reddit_limit = params.get("reddit_limit", 30)
    youtube_limit = params.get("youtube_limit", 30)
    twitter_limit = params.get("twitter_limit", 30)
    
    def run_pipeline():
        global task_status
        task_status["is_running"] = True
        task_status["current_task"] = f"manual_{keyword}"
        task_status["last_update"] = int(time.time())
        
        try:
            from collect import run_collection
            from ai_analysis import run_analysis
            
            task_status["progress"] = f"正在采集数据: {keyword}"
            logger.info(f"Starting collection for: {keyword}")
            run_collection(keyword, language, reddit_limit, youtube_limit, twitter_limit)
            
            task_status["progress"] = "正在进行 AI 分析..."
            logger.info("Starting AI analysis")
            run_analysis(language=language, keyword=keyword)
            
            task_status["progress"] = "任务完成！"
            logger.info("Pipeline completed successfully")
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            task_status["progress"] = f"任务失败: {str(e)}"
        finally:
            task_status["is_running"] = False
            task_status["last_update"] = int(time.time())

    background_tasks.add_task(run_pipeline)
    return {"status": "accepted", "message": "Collection and analysis started in background"}

# 获取任务状态
@app.get("/api/task-status")
async def get_task_status():
    return task_status


# --- 订阅相关 API ---

@app.get("/api/subscriptions")
async def get_subscriptions():
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500)
    try:
        subs = conn.execute("SELECT * FROM subscriptions ORDER BY id DESC").fetchall()
        return [dict(row) for row in subs]
    finally:
        conn.close()

@app.post("/api/subscriptions")
async def create_subscription(params: dict):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500)
    try:
        keyword = params.get("keyword")
        if not keyword: raise HTTPException(status_code=400, detail="Keyword required")
        
        # 计算间隔秒数
        interval_seconds = params.get("interval_seconds", 21600)  # 默认 6 小时
        
        conn.execute("""
            INSERT INTO subscriptions (keyword, language, reddit_limit, youtube_limit, twitter_limit, interval_seconds, next_run)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            keyword,
            params.get("language", "en"),
            params.get("reddit_limit", 30),
            params.get("youtube_limit", 30),
            params.get("twitter_limit", 30),
            interval_seconds,
            int(time.time()) # 立即运行一次? 或者稍后. 这里设为当前时间意味着下次检查会立即触发
        ))
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()

@app.delete("/api/subscriptions/{id}")
async def delete_subscription(id: int):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500)
    try:
        conn.execute("DELETE FROM subscriptions WHERE id = ?", (id,))
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()

@app.get("/api/alerts")
async def get_alerts():
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500)
    try:
        alerts = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50").fetchall()
        return [dict(row) for row in alerts]
    finally:
        conn.close()

@app.post("/api/clear-data")
async def clear_data():
    """清空所有采集数据和分析报告"""
    try:
        # 1. 删除报告文件
        if os.path.exists(REPORT_FILE):
            os.remove(REPORT_FILE)
            logger.info(f"Deleted {REPORT_FILE}")
        
        # 2. 清空数据库表
        conn = get_db_connection()
        if conn:
            try:
                conn.execute("DELETE FROM cleaned_data")
                conn.commit()
                logger.info("Cleared cleaned_data table")
            except Exception as e:
                logger.warning(f"Error clearing cleaned_data: {e}")
            finally:
                conn.close()
        
        return {"status": "ok", "message": "所有数据已清空"}
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)

