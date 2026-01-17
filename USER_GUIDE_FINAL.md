# 多关键词分析系统 - 使用指南

## 系统特性

✅ **完全隔离**：每个关键词的数据和分析完全独立
✅ **自动刷新**：采集完成后自动更新所有页面
✅ **历史保留**：每个关键词的分析报告都会保存
✅ **精准匹配**：思维导图、观点、摘要都围绕关键词

## 使用流程

### 1. 采集第一个关键词

1. 打开前端应用
2. 在仪表盘点击右上角 "+" 按钮
3. 输入关键词：`Python`
4. 设置采集参数（或使用默认值）
5. 点击"开始采集"

**后台处理：**
- 采集 Reddit、YouTube、Twitter 数据
- 保存到数据库（keyword = "Python"）
- AI 分析生成报告
- 保存到 `analysis_report_Python.json`

**前端显示：**
- 仪表盘显示 Python 的分析结果
- 思维导图：`A[Python] --> ...`
- 核心观点：关于 Python 的观点
- AI 摘要：关于 Python 的摘要
- 源数据：Python 相关的帖子

### 2. 采集第二个关键词

1. 返回仪表盘
2. 再次点击 "+" 按钮
3. 输入关键词：`JavaScript`
4. 点击"开始采集"

**后台处理：**
- 采集 JavaScript 相关数据
- 保存到数据库（keyword = "JavaScript"）
- AI 分析生成新报告
- 保存到 `analysis_report_JavaScript.json`
- **重要**：`analysis_report_Python.json` 仍然保留

**前端显示：**
- 仪表盘自动更新为 JavaScript 的数据
- 思维导图：`A[JavaScript] --> ...`
- 核心观点：关于 JavaScript 的观点
- AI 摘要：关于 JavaScript 的摘要
- 源数据：JavaScript 相关的帖子

### 3. 查看不同关键词的数据

**当前实现：**
- 系统自动显示最新采集的关键词
- 切换到源数据页面会自动刷新
- 显示最新关键词的数据

**未来扩展：**
- 可以添加关键词选择器
- 用户可以手动切换查看不同关键词
- 所有历史分析都已保存

## 数据隔离验证

### 验证方法 1：查看文件

检查项目根目录：
```
analysis_report_Python.json      ← Python 的分析报告
analysis_report_JavaScript.json  ← JavaScript 的分析报告
analysis_report_Gemini.json      ← Gemini 的分析报告
```

每个文件包含独立的分析结果。

### 验证方法 2：对比内容

1. 采集 "Python"
2. 记录思维导图的观点
3. 采集 "JavaScript"
4. 对比思维导图的观点

**预期结果：**
- Python 的观点：关于 Python 的特性、生态、应用等
- JavaScript 的观点：关于 JavaScript 的特性、框架、应用等
- 两者完全不同

### 验证方法 3：运行测试

```bash
python test_report_isolation.py
```

测试会自动：
1. 采集两个不同的关键词
2. 对比分析结果
3. 验证是否正确隔离

## 技术细节

### 数据库结构

```sql
CREATE TABLE cleaned_data (
    id INTEGER PRIMARY KEY,
    platform TEXT,
    content TEXT,
    author TEXT,
    timestamp TEXT,
    engagement TEXT,
    url TEXT,
    keyword TEXT  -- 关键字段
);
```

每条数据都标记了关键词。

### 报告文件命名

```python
# 关键词 "Python"
report_file = "analysis_report_Python.json"

# 关键词 "JavaScript"
report_file = "analysis_report_JavaScript.json"

# 无关键词（向后兼容）
report_file = "analysis_report.json"
```

### API 查询逻辑

```python
# 1. 获取最新关键词
SELECT keyword FROM cleaned_data 
WHERE keyword != 'unknown' 
ORDER BY rowid DESC LIMIT 1

# 2. 读取对应的报告文件
report_file = f"analysis_report_{keyword}.json"

# 3. 返回匹配的数据
```

## 常见问题

### Q1: 为什么切换到源数据页面会重新加载？

**A:** 这是设计行为。每次切换标签页，页面会重新创建并刷新数据，确保显示最新的内容。

### Q2: 旧关键词的数据会被删除吗？

**A:** 不会。每个关键词的数据和分析报告都会保留在：
- 数据库：`cleaned_data` 表（按 keyword 字段区分）
- 报告文件：`analysis_report_{keyword}.json`

### Q3: 如何查看历史关键词的分析？

**A:** 当前版本自动显示最新关键词。如需查看历史数据，可以：
1. 直接打开对应的 JSON 文件查看
2. 未来版本会添加关键词选择器

### Q4: 思维导图为什么有时显示不正确？

**A:** 确保：
1. AI 分析已完成（等待任务完成提示）
2. 报告文件已生成
3. 刷新页面或切换标签页

### Q5: 如何清空所有数据？

**A:** 在仪表盘点击右上角三个点 → "清空所有数据"

## 测试建议

### 基础测试
1. 采集 "Python"
2. 查看仪表盘和源数据
3. 采集 "JavaScript"
4. 再次查看仪表盘和源数据
5. 验证数据已更新

### 完整测试
```bash
# 1. 清空旧数据
python clear_old_data.py

# 2. 测试关键词隔离
python test_keyword_isolation.py

# 3. 测试报告隔离
python test_report_isolation.py

# 4. 测试关键词切换
python test_keyword_switch.py
```

## 总结

系统现在完全支持多关键词独立分析：

✅ 数据按关键词隔离存储
✅ 分析报告按关键词独立保存
✅ 前端自动显示最新关键词
✅ 思维导图、观点、摘要完全匹配关键词
✅ 不同关键词的数据不会互相干扰

每次采集新关键词，系统都会生成完全独立的分析结果！
