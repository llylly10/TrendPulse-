# 关键词隔离功能说明

## ✅ 已实现的功能

系统现在完全支持多关键词独立分析，每个关键词的数据互不干扰。

## 工作原理

### 1. 数据存储
- `cleaned_data` 表新增 `keyword` 字段
- 每条数据都标记所属的关键词
- 不同关键词的数据独立存储

### 2. 数据采集
- 采集时传递关键词参数
- 数据清洗时保存关键词
- AI 分析时按关键词过滤

### 3. 数据展示
- 仪表盘自动显示**最新关键词**的数据
- 源数据页面显示**最新关键词**的数据
- 每次采集新关键词后，前端自动切换显示

## 测试结果

运行 `python test_keyword_isolation.py` 的结果：

```
✓ Gemini 采集完成
  - 总帖子数: 286
  - 情感得分: 52.0
  - 关键词: Gemini

✓ ChatGPT 采集完成
  - 总帖子数: 296
  - 情感得分: 57.0
  - 关键词: ChatGPT

✓ 数据库验证
  - Gemini: 286 条
  - ChatGPT: 296 条
  - 数据完全隔离 ✓
```

## 使用示例

### 场景1：分析不同产品
```
1. 采集 "Gemini" 关键词
   → 仪表盘显示 Gemini 的舆情分析

2. 采集 "ChatGPT" 关键词
   → 仪表盘自动切换到 ChatGPT 的分析

3. 采集 "Claude" 关键词
   → 仪表盘自动切换到 Claude 的分析
```

### 场景2：定时监控多个关键词
```
1. 创建订阅：Gemini (每6小时)
2. 创建订阅：ChatGPT (每6小时)
3. 创建订阅：Claude (每6小时)

系统会：
- 自动定期采集每个关键词
- 分别分析每个关键词的舆情
- 仪表盘显示最新采集的关键词
```

## 数据流程

```
用户输入关键词 "Gemini"
    ↓
采集 Reddit/YouTube/Twitter 数据
    ↓
数据清洗，标记 keyword = "Gemini"
    ↓
AI 分析，只分析 keyword = "Gemini" 的数据
    ↓
生成分析报告
    ↓
仪表盘显示 Gemini 的分析结果
```

## API 变化

### Dashboard API
```
GET /api/dashboard?keyword=Gemini
```
- 不传 keyword：自动显示最新关键词
- 传 keyword：显示指定关键词的数据

### Source Data API
```
GET /api/source-data?keyword=Gemini
```
- 不传 keyword：自动显示最新关键词
- 传 keyword：显示指定关键词的数据

## 数据库变化

### cleaned_data 表
```sql
CREATE TABLE cleaned_data (
    platform TEXT,
    raw_id TEXT,
    content TEXT,
    author TEXT,
    timestamp TEXT,
    engagement TEXT,
    url TEXT,
    keyword TEXT  -- 新增字段
)
```

### 迁移脚本
```bash
python migrate_add_keyword.py
```

## 前端显示

### 仪表盘
- 自动显示最新关键词的数据
- 标题显示当前关键词
- 所有图表和统计都是该关键词的数据

### 思维导图
- 核心主题显示关键词
- 观点分布是该关键词的分析结果
- 情感颜色基于该关键词的数据

### 源数据
- 只显示当前关键词的原始数据
- 可以看到每条数据的关键词标签

## 注意事项

1. **旧数据处理**
   - 旧数据的 keyword 会被设置为 'unknown'
   - 建议清空旧数据：`python clear_old_data.py`

2. **分析报告**
   - 目前分析报告是全局的（`analysis_report.json`）
   - 每次分析会覆盖上一次的报告
   - 仪表盘显示的是最新的分析结果

3. **最新关键词逻辑**
   - 系统自动获取数据库中最新插入的关键词
   - 基于 rowid 排序，最新的在最前面

## 测试工具

### 1. 关键词隔离测试
```bash
python test_keyword_isolation.py
```
- 测试两个不同关键词
- 验证数据隔离
- 检查仪表盘切换

### 2. 清空旧数据
```bash
python clear_old_data.py
```
- 删除分析报告
- 清空 cleaned_data 表
- 准备测试新功能

### 3. 检查数据库
```bash
python check_subscriptions.py
```
- 查看所有订阅
- 检查关键词分布

## 故障排查

### 问题1：仪表盘显示旧关键词的数据
**原因**：缓存或数据未刷新
**解决**：
1. 刷新页面
2. 检查后端日志
3. 确认数据库中有新关键词的数据

### 问题2：不同关键词的数据混在一起
**原因**：数据清洗时未正确标记关键词
**解决**：
1. 检查 `data_cleaning.py` 是否传递了 keyword
2. 检查 `collect.py` 是否调用了 `process_data(keyword)`
3. 清空数据重新测试

### 问题3：思维导图显示错误的内容
**原因**：AI 分析时未按关键词过滤
**解决**：
1. 检查 `ai_analysis.py` 的 SQL 查询
2. 确认传递了正确的 keyword 参数
3. 重新运行分析

## 未来改进

1. **多关键词对比**
   - 在一个页面对比多个关键词
   - 显示趋势对比图表

2. **关键词选择器**
   - 前端添加下拉菜单
   - 用户可以切换查看不同关键词

3. **历史数据**
   - 保存每个关键词的历史分析
   - 显示舆情变化趋势

4. **关键词管理**
   - 查看所有已采集的关键词
   - 删除特定关键词的数据

## 总结

✅ **完全支持多关键词**
- 每个关键词独立存储
- 每个关键词独立分析
- 仪表盘自动显示最新关键词

✅ **数据完全隔离**
- Gemini 的数据不会影响 ChatGPT
- 每个关键词有自己的分析结果
- 思维导图和统计都是独立的

✅ **测试验证通过**
- 两个关键词同时存在
- 数据正确隔离
- 仪表盘正确切换

现在系统可以正确处理任意关键词，不再局限于 DeepSeek！🎉
