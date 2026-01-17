# 源数据页面更新问题修复说明

## 问题：源数据不会随关键词变化而更新

### 之前的问题

```
用户操作流程：
1. 在仪表盘采集 "DeepSeek" → 看到 DeepSeek 的数据 ✓
2. 切换到源数据页面 → 看到 DeepSeek 的数据 ✓
3. 返回仪表盘，采集 "Gemini" → 看到 Gemini 的数据 ✓
4. 切换到源数据页面 → 还是看到 DeepSeek 的数据 ✗

问题：源数据页面没有更新！
```

### 原因

```
前端页面结构（修复前）：

MainNavigation
├─ _pages = [
│    DashboardPage(),      ← 创建一次，保存在内存
│    SourceDataPage(),     ← 创建一次，保存在内存
│    SubscriptionPage()    ← 创建一次，保存在内存
│  ]
└─ 显示: _pages[_selectedIndex]

切换标签时：
- 只改变 _selectedIndex
- 不重新创建页面
- SourceDataPage 的 initState() 不会再次调用
- 数据不会刷新
```

### 解决方案

```
前端页面结构（修复后）：

MainNavigation
├─ _getPage(index) {
│    switch (index) {
│      case 0: return DashboardPage();      ← 每次都创建新实例
│      case 1: return SourceDataPage();     ← 每次都创建新实例
│      case 2: return SubscriptionPage();   ← 每次都创建新实例
│    }
│  }
└─ 显示: _getPage(_selectedIndex)

切换标签时：
- 调用 _getPage() 创建新页面
- 页面的 initState() 被调用
- 自动刷新数据
- 显示最新内容
```

## 修复后的流程

```
用户操作流程：
1. 在仪表盘采集 "DeepSeek"
   └─> 后端保存数据 (keyword = "DeepSeek")
   └─> 仪表盘显示 DeepSeek 数据 ✓

2. 切换到源数据页面
   └─> 创建新的 SourceDataPage
   └─> initState() 调用 refreshSourceData()
   └─> API 返回最新关键词 "DeepSeek" 的数据
   └─> 显示 DeepSeek 数据 ✓

3. 返回仪表盘，采集 "Gemini"
   └─> 后端保存数据 (keyword = "Gemini")
   └─> 仪表盘显示 Gemini 数据 ✓

4. 切换到源数据页面
   └─> 创建新的 SourceDataPage（重要！）
   └─> initState() 调用 refreshSourceData()
   └─> API 返回最新关键词 "Gemini" 的数据
   └─> 显示 Gemini 数据 ✓

完美！数据正确更新了！
```

## 数据流程图

```
采集新关键词 "Gemini"
        ↓
后端保存到数据库
(keyword = "Gemini")
        ↓
任务完成，DataProvider 更新
        ↓
用户切换到源数据页面
        ↓
创建新的 SourceDataPage ← 关键修复点
        ↓
initState() 被调用
        ↓
refreshSourceData()
        ↓
GET /api/source-data
        ↓
后端查询最新关键词
SELECT * WHERE keyword = "Gemini"
        ↓
返回 Gemini 的数据
        ↓
UI 显示 Gemini 的数据 ✓
```

## 修改的文件

### 1. frontend/lib/main.dart

```dart
// 修改前
final List<Widget> _pages = [DashboardPage(), SourceDataPage(), ...];
body: _pages[_selectedIndex]

// 修改后
Widget _getPage(int index) {
  switch (index) {
    case 0: return DashboardPage();
    case 1: return SourceDataPage();
    case 2: return SubscriptionPage();
  }
}
body: _getPage(_selectedIndex)
```

### 2. frontend/lib/pages/source_data_page.dart

保持不变，确认 initState() 中有数据刷新逻辑：

```dart
@override
void initState() {
  super.initState();
  Future.microtask(() =>
    Provider.of<DataProvider>(context, listen: false).refreshSourceData());
}
```

## 验证修复

### 快速测试
```bash
python test_keyword_switch.py
```

### 手动测试
1. 采集关键词 "Python"
2. 查看源数据 → 应该显示 Python 相关内容
3. 采集关键词 "JavaScript"  
4. 查看源数据 → 应该显示 JavaScript 相关内容（不是 Python）

## 总结

**问题**：页面被缓存，不会自动刷新

**解决**：每次切换都重新创建页面

**结果**：数据始终保持最新，用户体验完美！

---

## 技术要点

### 为什么这样修复？

1. **简单有效**：只改了几行代码
2. **符合预期**：用户期望看到最新数据
3. **易于维护**：逻辑清晰，不需要复杂的状态管理
4. **性能可接受**：页面很轻量，重新创建的开销很小

### 有没有其他方案？

有，但都更复杂：

1. **使用 PageView + PageController**
   - 需要监听页面切换事件
   - 需要手动管理刷新逻辑
   - 代码更复杂

2. **使用 IndexedStack + VisibilityDetector**
   - 需要额外的依赖
   - 需要监听可见性变化
   - 代码更复杂

3. **使用全局事件总线**
   - 需要实现事件系统
   - 需要管理订阅和取消订阅
   - 代码更复杂

当前方案是最简单、最直接的解决方案！
