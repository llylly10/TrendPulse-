# 源数据页面更新问题 - 快速修复总结

## 问题
源数据页面不会随着关键词变化而更新

## 原因
页面被缓存在内存中，切换标签时不会重新加载数据

## 修复
修改了 2 个文件：

### 1. `frontend/lib/main.dart`
将固定的页面列表改为动态创建：
```dart
// 之前：页面被缓存
final List<Widget> _pages = [DashboardPage(), SourceDataPage(), ...];
body: _pages[_selectedIndex]

// 现在：每次切换都重新创建
Widget _getPage(int index) { ... }
body: _getPage(_selectedIndex)
```

### 2. `frontend/lib/pages/source_data_page.dart`
保持简洁，在 `initState()` 中刷新数据（每次页面创建时都会调用）

## 效果
- ✓ 切换到源数据页面时自动刷新
- ✓ 显示最新关键词的数据
- ✓ 不需要手动点击刷新按钮

## 测试
```bash
python test_keyword_switch.py
```

## 使用
1. 在仪表盘采集新关键词
2. 等待任务完成
3. 切换到源数据页面 → 自动显示新数据
