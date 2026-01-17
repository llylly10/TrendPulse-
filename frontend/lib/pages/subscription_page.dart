import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/data_provider.dart';
import '../models/subscription.dart';
import '../utils/theme_utils.dart';

class SubscriptionPage extends StatefulWidget {
  @override
  _SubscriptionPageState createState() => _SubscriptionPageState();
}

class _SubscriptionPageState extends State<SubscriptionPage> {
  final _keywordController = TextEditingController();
  String _language = 'en';
  final _redditLimitController = TextEditingController(text: '30');
  final _youtubeLimitController = TextEditingController(text: '30');
  final _twitterLimitController = TextEditingController(text: '30');
  final _hoursController = TextEditingController(text: '0');
  final _minutesController = TextEditingController(text: '1');
  final _secondsController = TextEditingController(text: '0');

  @override
  void initState() {
    super.initState();
    Future.microtask(() =>
        Provider.of<DataProvider>(context, listen: false).fetchSubscriptions());
  }

  @override
  void dispose() {
    _keywordController.dispose();
    _redditLimitController.dispose();
    _youtubeLimitController.dispose();
    _twitterLimitController.dispose();
    _hoursController.dispose();
    _minutesController.dispose();
    _secondsController.dispose();
    super.dispose();
  }

  void _showAddDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('新建定时任务'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _keywordController,
                decoration: const InputDecoration(
                  labelText: '关键词',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _language,
                decoration: const InputDecoration(
                  labelText: '语言',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'en', child: Text('英文 (en)')),
                  DropdownMenuItem(value: 'zh', child: Text('中文 (zh)')),
                ],
                onChanged: (val) => setState(() => _language = val!),
              ),
              const SizedBox(height: 16),
              const Text(
                '执行间隔',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _hoursController,
                      decoration: const InputDecoration(
                        labelText: '时',
                        border: OutlineInputBorder(),
                        suffixText: 'h',
                      ),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _minutesController,
                      decoration: const InputDecoration(
                        labelText: '分',
                        border: OutlineInputBorder(),
                        suffixText: 'm',
                      ),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _secondsController,
                      decoration: const InputDecoration(
                        labelText: '秒',
                        border: OutlineInputBorder(),
                        suffixText: 's',
                      ),
                      keyboardType: TextInputType.number,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                '采集数量',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                      child: TextField(
                          controller: _redditLimitController,
                          decoration:
                              const InputDecoration(
                                labelText: 'Reddit',
                                border: OutlineInputBorder(),
                              ),
                          keyboardType: TextInputType.number,
                      )),
                  const SizedBox(width: 8),
                  Expanded(
                      child: TextField(
                          controller: _youtubeLimitController,
                          decoration:
                              const InputDecoration(
                                labelText: 'YouTube',
                                border: OutlineInputBorder(),
                              ),
                          keyboardType: TextInputType.number,
                      )),
                  const SizedBox(width: 8),
                  Expanded(
                      child: TextField(
                          controller: _twitterLimitController,
                          decoration:
                              const InputDecoration(
                                labelText: 'Twitter',
                                border: OutlineInputBorder(),
                              ),
                          keyboardType: TextInputType.number,
                      )),
                ],
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () {
              if (_keywordController.text.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('请输入关键词')),
                );
                return;
              }
              
              // 计算总秒数
              final hours = int.tryParse(_hoursController.text) ?? 0;
              final minutes = int.tryParse(_minutesController.text) ?? 0;
              final seconds = int.tryParse(_secondsController.text) ?? 0;
              final totalSeconds = hours * 3600 + minutes * 60 + seconds;
              
              if (totalSeconds < 10) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('间隔时间至少 10 秒')),
                );
                return;
              }
              
              Provider.of<DataProvider>(context, listen: false)
                  .createSubscription(
                _keywordController.text,
                _language,
                int.tryParse(_redditLimitController.text) ?? 30,
                int.tryParse(_youtubeLimitController.text) ?? 30,
                int.tryParse(_twitterLimitController.text) ?? 30,
                totalSeconds,
              );
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('✓ 定时任务已创建'),
                  backgroundColor: Colors.green,
                ),
              );
            },
            child: const Text('创建'),
          ),
        ],
      ),
    );
  }

  void _showDeleteConfirmDialog(BuildContext context, DataProvider provider, int id) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning, color: Colors.orange),
            SizedBox(width: 8),
            Text('确认删除'),
          ],
        ),
        content: const Text('确定要删除这个定时任务吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () {
              provider.deleteSubscription(id);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('✓ 已删除'),
                  backgroundColor: Colors.green,
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('删除'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('定时任务管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _showAddDialog,
          ),
        ],
      ),
      body: Consumer<DataProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.subscriptions.isEmpty) {
            return const Center(child: Text('暂无定时任务'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.subscriptions.length,
            itemBuilder: (context, index) {
              final sub = provider.subscriptions[index];
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: ThemeUtils.getCardColor(context),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: ThemeUtils.getCardBorderColor(context)),
                  boxShadow: ThemeUtils.getCardShadow(context),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  title: Text(
                    sub.keyword,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      '间隔: ${sub.intervalDisplay} | 下次: ${DateTime.fromMillisecondsSinceEpoch(sub.nextRun * 1000).toString().split('.')[0]}',
                      style: TextStyle(
                        fontSize: 13,
                        color: ThemeUtils.getSecondaryTextColor(context),
                      ),
                    ),
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete, color: Colors.redAccent),
                    onPressed: () => _showDeleteConfirmDialog(context, provider, sub.id),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
