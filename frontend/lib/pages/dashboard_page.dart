import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import '../providers/data_provider.dart';
import '../widgets/topic_cards.dart';
import '../main.dart' show ThemeProvider;
import '../utils/theme_utils.dart';

class DashboardPage extends StatefulWidget {
  @override
  _DashboardPageState createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final _keywordController = TextEditingController(text: 'DeepSeek');
  String _language = 'en';
  final _redditLimitController = TextEditingController(text: '30');
  final _youtubeLimitController = TextEditingController(text: '30');
  final _twitterLimitController = TextEditingController(text: '30');
  bool _isExpanded = false;
  
  // 跟踪任务状态，避免重复显示 SnackBar
  bool _wasTaskRunning = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(() =>
        Provider.of<DataProvider>(context, listen: false).refreshDashboard());
  }

  @override
  void dispose() {
    _keywordController.dispose();
    _redditLimitController.dispose();
    _youtubeLimitController.dispose();
    _twitterLimitController.dispose();
    super.dispose();
  }

  void _showAlertsDialog(BuildContext context, DataProvider provider) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('报警通知'),
        content: SizedBox(
          width: double.maxFinite,
          child: provider.alerts.isEmpty
              ? const Text('暂无报警')
              : ListView.builder(
                  shrinkWrap: true,
                  itemCount: provider.alerts.length,
                  itemBuilder: (context, index) {
                    final alert = provider.alerts[index];
                    return ListTile(
                      leading: const Icon(Icons.warning, color: Colors.red),
                      title: Text(alert.message),
                      subtitle: Text(DateTime.fromMillisecondsSinceEpoch(
                              alert.createdAt * 1000)
                          .toString()),
                    );
                  },
                ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context), child: const Text('关闭')),
        ],
      ),
    );
  }

  void _showClearDataDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning, color: Colors.orange),
            SizedBox(width: 8),
            Text('确认清空数据'),
          ],
        ),
        content: const Text(
          '此操作将清空所有采集数据和分析报告，但不会删除订阅任务和报警记录。\n\n确定要继续吗？',
          style: TextStyle(height: 1.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              final provider = Provider.of<DataProvider>(context, listen: false);
              await provider.clearAllData();
              await provider.refreshDashboard();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('✓ 数据已清空'),
                    backgroundColor: Colors.green,
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('确认清空'),
          ),
        ],
      ),
    );
  }

  void _showThemeDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('选择主题'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.brightness_5),
              title: const Text('亮色'),
              onTap: () {
                Provider.of<ThemeProvider>(context, listen: false)
                    .setThemeMode(ThemeMode.light);
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.brightness_2),
              title: const Text('暗色'),
              onTap: () {
                Provider.of<ThemeProvider>(context, listen: false)
                    .setThemeMode(ThemeMode.dark);
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.brightness_auto),
              title: const Text('跟随系统'),
              onTap: () {
                Provider.of<ThemeProvider>(context, listen: false)
                    .setThemeMode(ThemeMode.system);
                Navigator.pop(context);
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title:
            const Text('舆情仪表盘', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          Consumer<DataProvider>(builder: (context, provider, _) {
            final unreadCount = provider.alerts.where((a) => !a.isRead).length;
            return Stack(
              children: [
                IconButton(
                  icon: const Icon(Icons.notifications),
                  onPressed: () => _showAlertsDialog(context, provider),
                ),
                if (unreadCount > 0)
                  Positioned(
                    right: 8,
                    top: 8,
                    child: Container(
                      padding: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        color: Colors.red,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      constraints: const BoxConstraints(
                        minWidth: 16,
                        minHeight: 16,
                      ),
                      child: Text(
                        '$unreadCount',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
              ],
            );
          }),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (value) {
              if (value == 'clear') {
                _showClearDataDialog(context);
              } else if (value == 'theme') {
                _showThemeDialog(context);
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'theme',
                child: Row(
                  children: [
                    Icon(Icons.palette),
                    SizedBox(width: 8),
                    Text('切换主题'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'clear',
                child: Row(
                  children: [
                    Icon(Icons.delete_sweep, color: Colors.red),
                    SizedBox(width: 8),
                    Text('清空所有数据'),
                  ],
                ),
              ),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => Provider.of<DataProvider>(context, listen: false)
                .refreshDashboard(),
          ),
        ],
      ),
      body: Consumer<DataProvider>(
        builder: (context, provider, child) {
          // 检测任务状态变化
          if (provider.isTaskRunning && !_wasTaskRunning) {
            // 任务刚开始
            _wasTaskRunning = true;
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) {
                ScaffoldMessenger.of(context).hideCurrentSnackBar();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Row(
                      children: [
                        const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Text(provider.taskProgress)),
                      ],
                    ),
                    duration: const Duration(seconds: 120),
                  ),
                );
              }
            });
          } else if (!provider.isTaskRunning && _wasTaskRunning) {
            // 任务刚完成
            _wasTaskRunning = false;
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) {
                ScaffoldMessenger.of(context).hideCurrentSnackBar();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Row(
                      children: [
                        Icon(Icons.check_circle, color: Colors.green),
                        SizedBox(width: 12),
                        Text('✓ 任务完成，数据已刷新'),
                      ],
                    ),
                    duration: Duration(seconds: 3),
                    backgroundColor: Colors.green,
                  ),
                );
                // 刷新仪表板数据
                provider.refreshDashboard();
              }
            });
          } else if (provider.isTaskRunning && _wasTaskRunning && provider.taskProgress.isNotEmpty) {
            // 任务运行中，更新进度（但不要太频繁）
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) {
                // 只在进度信息改变时才更新 SnackBar
                final currentSnackBar = ScaffoldMessenger.of(context).hideCurrentSnackBar();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Row(
                      children: [
                        const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Text(provider.taskProgress)),
                      ],
                    ),
                    duration: const Duration(seconds: 120),
                  ),
                );
              }
            });
          }
          
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 16),
                  Text('错误: ${provider.error}'),
                ],
              ),
            );
          }

          final data = provider.dashboardData;

          return RefreshIndicator(
            onRefresh: () => provider.refreshDashboard(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSearchCard(context),
                  const SizedBox(height: 24),
                  if (data == null)
                    const Center(child: Text('暂无数据，请发起采集任务'))
                  else ...[
                    _buildHeader('实时概览'),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                            child: _buildStatCard(
                                '总采集量',
                                data.totalPosts.toString(),
                                Icons.analytics,
                                Colors.blue)),
                        const SizedBox(width: 16),
                        Expanded(
                            child: _buildStatCard(
                                '热度指数',
                                data.heatIndex.toStringAsFixed(1),
                                Icons.whatshot,
                                Colors.orange)),
                      ],
                    ),
                    const SizedBox(height: 24),
                    _buildHeader('情感倾向分析'),
                    const SizedBox(height: 16),
                    _buildSentimentCard(
                        data.sentiment.score, data.sentiment.label),
                    const SizedBox(height: 32),
                    _buildHeader('思维导图'),
                    const SizedBox(height: 16),
                    _buildMindMapCard(data.mermaidGraph, data.sentiment.score, data.nodeSentiments),
                    const SizedBox(height: 32),
                    _buildHeader('核心观点提取'),
                    const SizedBox(height: 16),
                    ...data.keyPoints
                        .take(3)
                        .map((point) => _buildPointCard(point))
                        .toList(),
                    const SizedBox(height: 32),
                    _buildHeader('AI 深度摘要'),
                    const SizedBox(height: 16),
                    _buildSummaryCard(data.summary),
                    const SizedBox(height: 40),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSearchCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '新建采集任务',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon:
                      Icon(_isExpanded ? Icons.expand_less : Icons.expand_more),
                  onPressed: () {
                    setState(() {
                      _isExpanded = !_isExpanded;
                    });
                  },
                ),
              ],
            ),
            if (_isExpanded) ...[
              const SizedBox(height: 16),
              TextField(
                controller: _keywordController,
                decoration: const InputDecoration(
                  labelText: '查询关键词',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.search),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _language,
                decoration: const InputDecoration(
                  labelText: '语言',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.language),
                ),
                items: const [
                  DropdownMenuItem(value: 'en', child: Text('英文 (en)')),
                  DropdownMenuItem(value: 'zh', child: Text('中文 (zh)')),
                ],
                onChanged: (val) => setState(() => _language = val!),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _redditLimitController,
                      decoration: const InputDecoration(
                        labelText: 'Reddit 条数',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _youtubeLimitController,
                      decoration: const InputDecoration(
                        labelText: 'YouTube 条数',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _twitterLimitController,
                      decoration: const InputDecoration(
                        labelText: 'Twitter 条数',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {
                    final provider =
                        Provider.of<DataProvider>(context, listen: false);
                    
                    setState(() {
                      _isExpanded = false;
                    });
                    
                    provider.startCollection(
                      _keywordController.text,
                      _language,
                      int.tryParse(_redditLimitController.text) ?? 30,
                      int.tryParse(_youtubeLimitController.text) ?? 30,
                      int.tryParse(_twitterLimitController.text) ?? 30,
                    );
                  },
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('开始采集与分析'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: Colors.indigo,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.bold,
        letterSpacing: 0.5,
      ),
    );
  }

  Widget _buildStatCard(
      String label, String value, IconData icon, Color color) {
    return Card(
      elevation: Theme.of(context).brightness == Brightness.dark ? 0 : 1,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 16),
            Text(label,
                style: TextStyle(
                    color: ThemeUtils.getSecondaryTextColor(context), 
                    fontSize: 14)),
            const SizedBox(height: 4),
            Text(value,
                style:
                    const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildSentimentCard(double score, String label) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final color =
        score > 60 ? Colors.green : (score < 40 ? Colors.red : Colors.orange);
    return Card(
      elevation: isDark ? 0 : 1,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('综合情感得分',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: color.withOpacity(0.5)),
                  ),
                  child: Text(
                    label,
                    style: TextStyle(
                        color: color,
                        fontWeight: FontWeight.bold,
                        fontSize: 12),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  height: 120,
                  width: 120,
                  child: CircularProgressIndicator(
                    value: score / 100,
                    strokeWidth: 12,
                    backgroundColor: isDark 
                        ? Colors.white.withOpacity(0.05)
                        : Colors.black.withOpacity(0.05),
                    valueColor: AlwaysStoppedAnimation<Color>(color),
                    strokeCap: StrokeCap.round,
                  ),
                ),
                Text(
                  '${score.toStringAsFixed(0)}',
                  style: const TextStyle(
                      fontSize: 32, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildSentimentLabel('负面', Colors.red),
                _buildSentimentLabel('中性', Colors.orange),
                _buildSentimentLabel('正面', Colors.green),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSentimentLabel(String text, Color color) {
    return Row(
      children: [
        Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(text,
            style:
                TextStyle(color: ThemeUtils.getSecondaryTextColor(context), fontSize: 12)),
      ],
    );
  }

  Widget _buildMindMapCard(String mermaidCode, double sentimentScore, Map<String, String> nodeSentiments) {
    return Card(
      elevation: Theme.of(context).brightness == Brightness.dark ? 0 : 1,
      child: Container(
        constraints: const BoxConstraints(minHeight: 300),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '观点分布',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                Row(
                  children: [
                    _buildLegendItem('正面', const Color(0xFF43A047)),
                    const SizedBox(width: 12),
                    _buildLegendItem('中性', const Color(0xFFFFA726)),
                    const SizedBox(width: 12),
                    _buildLegendItem('负面', const Color(0xFFE53935)),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 20),
            mermaidCode.isEmpty
                ? const Center(
                    child: Padding(
                      padding: EdgeInsets.all(40),
                      child: Text('暂无思维导图数据'),
                    ),
                  )
                : TopicCards(
                    mermaidCode: mermaidCode,
                    sentimentScore: sentimentScore,
                    nodeSentiments: nodeSentiments,
                  ),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: ThemeUtils.getSecondaryTextColor(context),
          ),
        ),
      ],
    );
  }

  Widget _buildPointCard(String point) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: ThemeUtils.getCardColor(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ThemeUtils.getCardBorderColor(context)),
        boxShadow: ThemeUtils.getCardShadow(context),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.auto_awesome, color: Colors.indigoAccent, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              point,
              style: const TextStyle(fontSize: 15, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(String summary) {
    return Card(
      elevation: Theme.of(context).brightness == Brightness.dark ? 0 : 1,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Colors.indigo.withOpacity(0.08),
              Colors.transparent,
            ],
          ),
        ),
        child: Text(
          summary,
          style: TextStyle(
            fontSize: 16,
            height: 1.6,
            color: ThemeUtils.getSecondaryTextColor(context),
          ),
        ),
      ),
    );
  }
}
