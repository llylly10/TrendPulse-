import 'package:flutter/material.dart';
import '../utils/theme_utils.dart';

class TopicCards extends StatelessWidget {
  final String mermaidCode;
  final double sentimentScore;
  final Map<String, String> nodeSentiments;

  const TopicCards({
    Key? key,
    required this.mermaidCode,
    this.sentimentScore = 50.0,
    this.nodeSentiments = const {},
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (mermaidCode.isEmpty) {
      return Center(
        child: Text(
          '暂无数据',
          style: TextStyle(
            color: ThemeUtils.getSecondaryTextColor(context),
          ),
        ),
      );
    }

    final mindMapData = _parseMermaidGraph(mermaidCode);

    if (mindMapData.nodes.isEmpty) {
      return Center(
        child: Text(
          '数据格式错误',
          style: TextStyle(
            color: ThemeUtils.getSecondaryTextColor(context),
          ),
        ),
      );
    }

    // 按情感分组
    final positiveNodes = <MindMapNode>[];
    final neutralNodes = <MindMapNode>[];
    final negativeNodes = <MindMapNode>[];

    for (var node in mindMapData.childNodes) {
      switch (node.sentiment.toLowerCase()) {
        case 'positive':
          positiveNodes.add(node);
          break;
        case 'negative':
          negativeNodes.add(node);
          break;
        default:
          neutralNodes.add(node);
      }
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 核心主题（根节点）
          if (mindMapData.rootNode != null)
            _buildRootNode(context, mindMapData.rootNode!),
          
          const SizedBox(height: 32),
          
          // 连接线
          _buildConnector(context),
          
          const SizedBox(height: 24),
          
          // 子节点按情感分组展示
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 正面观点
              if (positiveNodes.isNotEmpty)
                Expanded(
                  child: _buildSentimentGroup(
                    context,
                    '正面观点',
                    positiveNodes,
                    const Color(0xFF43A047),
                    Icons.sentiment_satisfied_alt,
                  ),
                ),
              
              if (positiveNodes.isNotEmpty && (neutralNodes.isNotEmpty || negativeNodes.isNotEmpty))
                const SizedBox(width: 16),
              
              // 中性观点
              if (neutralNodes.isNotEmpty)
                Expanded(
                  child: _buildSentimentGroup(
                    context,
                    '中性观点',
                    neutralNodes,
                    const Color(0xFFFFA726),
                    Icons.sentiment_neutral,
                  ),
                ),
              
              if (neutralNodes.isNotEmpty && negativeNodes.isNotEmpty)
                const SizedBox(width: 16),
              
              // 负面观点
              if (negativeNodes.isNotEmpty)
                Expanded(
                  child: _buildSentimentGroup(
                    context,
                    '负面观点',
                    negativeNodes,
                    const Color(0xFFE53935),
                    Icons.sentiment_dissatisfied,
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  MindMapData _parseMermaidGraph(String code) {
    final nodes = <String, MindMapNode>{};
    final edges = <MindMapEdge>[];
    String? rootId;

    // 解析节点定义 A[文本]
    final lines = code.split(';');
    for (var line in lines) {
      line = line.trim();
      if (line.isEmpty || line.startsWith('graph')) continue;

      final nodeMatches = RegExp(r'([A-Z]+)\[([^\]]+)\]').allMatches(line);
      for (var match in nodeMatches) {
        final id = match.group(1)!;
        final text = match.group(2)!;
        if (!nodes.containsKey(id)) {
          // 获取节点情感，如果没有则默认为 neutral
          final sentiment = nodeSentiments[id] ?? 'neutral';
          nodes[id] = MindMapNode(
            id: id,
            text: text,
            sentiment: sentiment,
          );
          rootId ??= id; // 第一个节点作为根节点
        }
      }

      // 解析边 A --> B
      final edgeMatch = RegExp(r'([A-Z]+)\s*-->\s*([A-Z]+)').firstMatch(line);
      if (edgeMatch != null) {
        edges.add(MindMapEdge(
          from: edgeMatch.group(1)!,
          to: edgeMatch.group(2)!,
        ));
      }
    }

    // 找出所有子节点（非根节点）
    final childNodes = <MindMapNode>[];
    if (rootId != null) {
      for (var node in nodes.values) {
        if (node.id != rootId) {
          childNodes.add(node);
        }
      }
    }

    return MindMapData(
      nodes: nodes,
      edges: edges,
      rootNode: rootId != null ? nodes[rootId] : null,
      childNodes: childNodes,
    );
  }

  Widget _buildRootNode(BuildContext context, MindMapNode node) {
    final color = _getSentimentColor(sentimentScore);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      constraints: const BoxConstraints(maxWidth: 500),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            color.withOpacity(0.15),
            color.withOpacity(0.05),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 2,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              _getSentimentIcon(sentimentScore),
              color: Colors.white,
              size: 32,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '核心主题',
                  style: TextStyle(
                    fontSize: 12,
                    color: ThemeUtils.getSecondaryTextColor(context),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  node.text,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: isDark ? Colors.white : Colors.black87,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              _getSentimentLabel(sentimentScore),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConnector(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 2,
          height: 30,
          color: ThemeUtils.getDividerColor(context),
        ),
        Icon(
          Icons.arrow_downward,
          size: 20,
          color: ThemeUtils.getSecondaryTextColor(context),
        ),
      ],
    );
  }

  Widget _buildSentimentGroup(
    BuildContext context,
    String title,
    List<MindMapNode> nodes,
    Color color,
    IconData icon,
  ) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Column(
      children: [
        // 分组标题
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: color.withOpacity(0.3),
              width: 1.5,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 6),
              Text(
                title,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : Colors.black87,
                ),
              ),
            ],
          ),
        ),
        
        const SizedBox(height: 16),
        
        // 节点列表
        ...nodes.map((node) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: _buildNodeCard(context, node, color),
        )).toList(),
      ],
    );
  }

  Widget _buildNodeCard(BuildContext context, MindMapNode node, Color color) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark 
            ? color.withOpacity(0.15)
            : color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withOpacity(isDark ? 0.5 : 0.4),
          width: 2,
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              node.text,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: isDark ? Colors.white : Colors.black87,
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Color _getSentimentColor(double score) {
    if (score >= 60) {
      return const Color(0xFF43A047);
    } else if (score < 40) {
      return const Color(0xFFE53935);
    } else {
      return const Color(0xFFFFA726);
    }
  }

  IconData _getSentimentIcon(double score) {
    if (score >= 60) {
      return Icons.sentiment_satisfied_alt;
    } else if (score < 40) {
      return Icons.sentiment_dissatisfied;
    } else {
      return Icons.sentiment_neutral;
    }
  }

  String _getSentimentLabel(double score) {
    if (score >= 60) {
      return '正面';
    } else if (score < 40) {
      return '负面';
    } else {
      return '中性';
    }
  }
}

class MindMapData {
  final Map<String, MindMapNode> nodes;
  final List<MindMapEdge> edges;
  final MindMapNode? rootNode;
  final List<MindMapNode> childNodes;

  MindMapData({
    required this.nodes,
    required this.edges,
    this.rootNode,
    required this.childNodes,
  });
}

class MindMapNode {
  final String id;
  final String text;
  final String sentiment;

  MindMapNode({
    required this.id,
    required this.text,
    this.sentiment = 'neutral',
  });
}

class MindMapEdge {
  final String from;
  final String to;

  MindMapEdge({required this.from, required this.to});
}
