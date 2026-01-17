import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/data_provider.dart';
import '../utils/theme_utils.dart';

class SourceDataPage extends StatefulWidget {
  @override
  _SourceDataPageState createState() => _SourceDataPageState();
}

class _SourceDataPageState extends State<SourceDataPage> {
  @override
  void initState() {
    super.initState();
    // 页面加载时刷新数据
    Future.microtask(() =>
        Provider.of<DataProvider>(context, listen: false).refreshSourceData());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title:
            const Text('源数据流', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => Provider.of<DataProvider>(context, listen: false)
                .refreshSourceData(),
          ),
        ],
      ),
      body: Consumer<DataProvider>(
        builder: (context, provider, child) {
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
          if (provider.sourcePosts.isEmpty) {
            return const Center(child: Text('暂无数据'));
          }

          // 获取当前关键词（从第一条数据中）
          final currentKeyword = provider.dashboardData?.keyword ?? '未知';

          return Column(
            children: [
              // 显示当前关键词
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                color: Theme.of(context).primaryColor.withOpacity(0.1),
                child: Row(
                  children: [
                    Icon(
                      Icons.label,
                      size: 18,
                      color: Theme.of(context).primaryColor,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '当前关键词: $currentKeyword',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Theme.of(context).primaryColor,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '${provider.sourcePosts.length} 条数据',
                      style: TextStyle(
                        fontSize: 12,
                        color: ThemeUtils.getSecondaryTextColor(context),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () => provider.refreshSourceData(),
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    itemCount: provider.sourcePosts.length,
                    itemBuilder: (context, index) {
                      final post = provider.sourcePosts[index];
                      return _buildPostItem(post);
                    },
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPostItem(dynamic post) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: ThemeUtils.getCardColor(context),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: ThemeUtils.getCardBorderColor(context)),
        boxShadow: ThemeUtils.getCardShadow(context),
      ),
      child: InkWell(
        onTap: () => _launchURL(post.url),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _buildPlatformIcon(post.platform),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          post.author,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 15),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          post.timestamp,
                          style: TextStyle(
                              fontSize: 12,
                              color: ThemeUtils.getDisabledTextColor(context)),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    Icons.open_in_new,
                    size: 18,
                    color: ThemeUtils.getDisabledTextColor(context),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                post.content,
                style: TextStyle(
                  fontSize: 14, 
                  height: 1.5,
                  color: ThemeUtils.getSecondaryTextColor(context),
                ),
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  _buildEngagementItem(Icons.favorite_border,
                      post.engagement['like_count']?.toString() ?? '0'),
                  const SizedBox(width: 16),
                  _buildEngagementItem(Icons.chat_bubble_outline,
                      post.engagement['num_comments']?.toString() ?? '0'),
                  const SizedBox(width: 16),
                  _buildEngagementItem(Icons.visibility_outlined,
                      post.engagement['view_count']?.toString() ?? '0'),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPlatformIcon(String platform) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    IconData iconData = Icons.article;
    Color color = Colors.grey;

    final p = platform.toLowerCase();
    if (p.contains('twitter') || p == 'x') {
      iconData = Icons.alternate_email;
      color = isDark ? Colors.white : const Color(0xFF1DA1F2); // Twitter蓝色
    } else if (p.contains('reddit')) {
      iconData = Icons.reddit;
      color = Colors.orange;
    } else if (p.contains('youtube')) {
      iconData = Icons.play_circle_filled;
      color = Colors.red;
    }

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(isDark ? 0.1 : 0.15),
        shape: BoxShape.circle,
      ),
      child: Icon(iconData, color: color, size: 20),
    );
  }

  Widget _buildEngagementItem(IconData icon, String value) {
    return Row(
      children: [
        Icon(
          icon, 
          size: 14, 
          color: ThemeUtils.getDisabledTextColor(context),
        ),
        const SizedBox(width: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 12, 
            color: ThemeUtils.getDisabledTextColor(context),
          ),
        ),
      ],
    );
  }

  Future<void> _launchURL(String urlString) async {
    if (urlString.isEmpty) return;
    final Uri url = Uri.parse(urlString);
    try {
      if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
        throw 'Could not launch $urlString';
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('无法打开链接: $urlString')),
        );
      }
    }
  }
}
