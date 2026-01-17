# 数据隔离 Bug 修复

## 问题描述

用户报告：搜索"河北"，但源数据流中显示的是 ChatGPT、Claude、Gemini、DeepSeek 等 AI 相关的内容。

## 根本原因

**`data_cleaning.py` 中的 `process_data()` 函数有严重 Bug！**

### 问题代码

```python
def process_data(keyword="unknown"):
    # 读取所有 Reddit 数据（没有过滤！）
    reddit_df = pd.read_sql_query(
        "SELECT * FROM reddit_submission",  # ❌ 读取所有数据
        conn
    )
    
    # 读取所有 YouTube 数据（没有过滤！）
    youtube_df = pd.read_sql_query(
        "SELECT * FROM youtube_video",  # ❌ 读取所有数据
        conn
    )
    
    # 读取所有 Twitter 数据（没有过滤！）
    twitter_df = pd.read_sql_query(
        "SELECT * FROM twitter_tweet",  # ❌ 读取所有数据
        conn
    )
    
    # 合并所有数据
    all_data = pd.concat([reddit_df, youtube_df, twitter_df])
    
    # 给所有数据打上新关键词的标签！
    final_df['keyword'] = keyword  # ❌ 所有旧数据都被标记成新关键词
```

### 问题流程

1. **第一次采集** - 关键词 "DeepSeek"
   - 采集 DeepSeek 相关数据 → 保存到 reddit_submission, youtube_video, twitter_tweet
   - 调用 `process_data("DeepSeek")`
   - 读取所有数据（只有 DeepSeek 的）
   - 标记 keyword = "DeepSeek"
   - 保存到 cleaned_data

2. **第二次采集** - 关键词 "河北"
   - 采集河北相关数据 → 保存到 reddit_submission, youtube_video, twitter_tweet
   - 调用 `process_data("河北")`
   - **读取所有数据（包括 DeepSeek 的旧数据！）**
   - **把所有数据都标记 keyword = "河北"**
   - 保存到 cleaned_data
   - **结果：河北的数据中包含了 DeepSeek 的内容！**

3. **第三次采集** - 关键词 "huggingface"
   - 采集 huggingface 相关数据
   - 调用 `process_data("huggingface")`
   - **读取所有数据（包括 DeepSeek 和河北的旧数据！）**
   - **把所有数据都标记 keyword = "huggingface"**
   - **结果：huggingface 的数据中包含了 DeepSeek 和河北的内容！**

### 数据库状态

```
cleaned_data 表:
- 498 条 keyword="河北" 的数据
  - 其中只有 34 条是真正关于河北的
  - 其他 464 条是 DeepSeek、huggingface 等旧数据被错误标记的

- 464 条 keyword="huggingface" 的数据
  - 其中只有 34 条是真正关于 huggingface 的
  - 其他 430 条是更早的旧数据被错误标记的
```

## 解决方案

### 修复 1: data_cleaning.py

添加 `task_ids` 参数，只处理指定任务的数据：

```python
def process_data(keyword="unknown", task_ids=None):
    # 如果指定了 task_ids，只处理这些任务的数据
    if task_ids:
        task_filter = f"WHERE task_id IN ({','.join(map(str, task_ids))})"
    else:
        task_filter = ""
    
    # 只读取指定任务的数据
    reddit_query = f"SELECT * FROM reddit_submission {task_filter}"
    reddit_df = pd.read_sql_query(reddit_query, conn)
    
    youtube_query = f"SELECT * FROM youtube_video {task_filter}"
    youtube_df = pd.read_sql_query(youtube_query, conn)
    
    twitter_query = f"SELECT * FROM twitter_tweet {task_filter}"
    twitter_df = pd.read_sql_query(twitter_query, conn)
    
    # 合并数据
    all_data = pd.concat([reddit_df, youtube_df, twitter_df])
    
    # 标记关键词
    final_df['keyword'] = keyword
```

### 修复 2: collect.py

传递 task_ids 给 process_data：

```python
def run_collection(keyword, language, reddit_limit, youtube_limit, twitter_limit):
    # 创建任务并采集数据
    reddit_task_id = create_task("reddit", keyword, language, reddit_limit)
    # ... 采集 Reddit 数据 ...
    
    youtube_task_id = create_task("youtube", keyword, language, youtube_limit)
    # ... 采集 YouTube 数据 ...
    
    twitter_task_id = create_task("twitter", keyword, language, twitter_limit)
    # ... 采集 Twitter 数据 ...
    
    # 只清洗当前任务的数据
    task_ids = [reddit_task_id, youtube_task_id, twitter_task_id]
    process_data(keyword, task_ids)  # ✅ 传递 task_ids
```

## 修复后的流程

1. **采集关键词 "河北"**
   - 创建 3 个任务：task_id = 142, 143, 144
   - 采集河北相关数据
   - 调用 `process_data("河北", [142, 143, 144])`
   - **只读取 task_id 在 [142, 143, 144] 的数据**
   - 标记 keyword = "河北"
   - **结果：只有河北的数据被保存**

2. **采集关键词 "Python"**
   - 创建 3 个任务：task_id = 145, 146, 147
   - 采集 Python 相关数据
   - 调用 `process_data("Python", [145, 146, 147])`
   - **只读取 task_id 在 [145, 146, 147] 的数据**
   - 标记 keyword = "Python"
   - **结果：只有 Python 的数据被保存，河北的数据不受影响**

## 需要的操作

### 1. 清空旧数据

由于现有的 cleaned_data 表中的数据已经被污染，需要清空：

```sql
DELETE FROM cleaned_data;
```

或者使用脚本：

```bash
python clear_old_data.py
```

### 2. 重新采集数据

清空后，重新采集所需的关键词：

```bash
# 前端操作：在仪表盘点击 "新建采集任务"
# 输入关键词，点击"开始采集"
```

### 3. 验证修复

运行测试脚本：

```bash
python test_data_isolation_fix.py
```

检查：
- 每个关键词的数据是否独立
- 内容是否与关键词相关
- 没有交叉污染

## 文件修改

- ✅ `data_cleaning.py` - 添加 task_ids 参数过滤
- ✅ `collect.py` - 传递 task_ids 参数

## 总结

这是一个严重的数据隔离 Bug：
- **原因**：数据清洗时读取了所有历史数据，并错误地标记成新关键词
- **影响**：每次采集都会把旧数据重新标记，导致数据完全混乱
- **修复**：只处理当前任务的数据，确保数据完全隔离

修复后，每个关键词的数据将完全独立，不会互相污染。
