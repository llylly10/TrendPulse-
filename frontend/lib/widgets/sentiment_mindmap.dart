import 'package:flutter/material.dart';
import 'dart:math' as math;

class SentimentMindMap extends StatelessWidget {
  final String mermaidCode;
  final double sentimentScore;

  const SentimentMindMap({
    Key? key,
    required this.mermaidCode,
    this.sentimentScore = 50.0,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (mermaidCode.isEmpty) {
      return const Center(child: Text('暂无思维导图数据'));
    }

    final nodes = _parseMermaidCode(mermaidCode);

    if (nodes.isEmpty) {
      return const Center(child: Text('思维导图格式错误'));
    }

    final brightness = Theme.of(context).brightness;

    return InteractiveViewer(
      boundaryMargin: const EdgeInsets.all(50),
      minScale: 0.5,
      maxScale: 2.0,
      child: CustomPaint(
        size: const Size(900, 500),
        painter: SentimentMindMapPainter(nodes, sentimentScore, brightness),
      ),
    );
  }

  List<MindMapNode> _parseMermaidCode(String code) {
    final nodes = <MindMapNode>[];
    final connections = <MapConnection>[];
    final nodeMap = <String, MindMapNode>{};

    final lines = code.split(';');

    for (var line in lines) {
      line = line.trim();
      if (line.isEmpty || line.startsWith('graph')) continue;

      final arrowMatch = RegExp(r'(\w+)(?:\[([^\]]+)\])?\s*-->\s*(\w+)(?:\[([^\]]+)\])?')
          .firstMatch(line);

      if (arrowMatch != null) {
        final fromId = arrowMatch.group(1)!;
        final fromLabel = arrowMatch.group(2) ?? fromId;
        final toId = arrowMatch.group(3)!;
        final toLabel = arrowMatch.group(4) ?? toId;

        if (!nodeMap.containsKey(fromId)) {
          nodeMap[fromId] = MindMapNode(id: fromId, label: fromLabel);
        }
        if (!nodeMap.containsKey(toId)) {
          nodeMap[toId] = MindMapNode(id: toId, label: toLabel);
        }

        connections.add(MapConnection(from: fromId, to: toId));
      }
    }

    if (nodeMap.isEmpty) return [];

    final childIds = connections.map((c) => c.to).toSet();
    final rootId = nodeMap.keys.firstWhere(
      (id) => !childIds.contains(id),
      orElse: () => nodeMap.keys.first,
    );

    _calculateHorizontalLayout(nodeMap, connections, rootId);

    return nodeMap.values.toList();
  }

  void _calculateHorizontalLayout(
    Map<String, MindMapNode> nodeMap,
    List<MapConnection> connections,
    String rootId,
  ) {
    final root = nodeMap[rootId]!;
    root.position = const Offset(100, 250);
    root.level = 0;

    for (var conn in connections) {
      final from = nodeMap[conn.from];
      final to = nodeMap[conn.to];
      if (from != null && to != null) {
        from.children.add(to);
      }
    }

    final children = connections
        .where((c) => c.from == rootId)
        .map((c) => nodeMap[c.to]!)
        .toList();

    if (children.isEmpty) return;

    final verticalSpacing = 80.0;
    final totalHeight = (children.length - 1) * verticalSpacing;
    final startY = 250 - totalHeight / 2;

    for (var i = 0; i < children.length; i++) {
      final child = children[i];
      child.level = 1;
      child.position = Offset(400, startY + i * verticalSpacing);
      child.parent = rootId;
    }
  }
}

class MindMapNode {
  final String id;
  final String label;
  Offset position;
  int level;
  String? parent;
  List<MindMapNode> children = [];

  MindMapNode({
    required this.id,
    required this.label,
    this.position = Offset.zero,
    this.level = 0,
    this.parent,
  });
}

class MapConnection {
  final String from;
  final String to;

  MapConnection({required this.from, required this.to});
}

class SentimentMindMapPainter extends CustomPainter {
  final List<MindMapNode> nodes;
  final double sentimentScore;
  final Brightness brightness;

  SentimentMindMapPainter(this.nodes, this.sentimentScore, this.brightness);

  @override
  void paint(Canvas canvas, Size size) {
    // 绘制连接线
    for (var node in nodes) {
      for (var child in node.children) {
        _drawConnection(canvas, node, child);
      }
    }

    // 绘制节点
    for (var node in nodes) {
      _drawNode(canvas, node);
    }
  }

  void _drawConnection(Canvas canvas, MindMapNode from, MindMapNode to) {
    final color = _getNodeColor(to);

    final path = Path();
    path.moveTo(from.position.dx + 80, from.position.dy);

    final controlPoint1 = Offset(
      from.position.dx + 150,
      from.position.dy,
    );
    final controlPoint2 = Offset(
      to.position.dx - 70,
      to.position.dy,
    );

    path.cubicTo(
      controlPoint1.dx,
      controlPoint1.dy,
      controlPoint2.dx,
      controlPoint2.dy,
      to.position.dx - 10,
      to.position.dy,
    );

    final linePaint = Paint()
      ..color = color.withOpacity(0.4)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke;

    canvas.drawPath(path, linePaint);

    // 绘制箭头
    _drawArrow(canvas, color, to.position.dx - 10, to.position.dy);
  }

  void _drawArrow(Canvas canvas, Color color, double x, double y) {
    final path = Path();
    path.moveTo(x, y);
    path.lineTo(x - 8, y - 6);
    path.lineTo(x - 8, y + 6);
    path.close();

    final arrowPaint = Paint()
      ..color = color.withOpacity(0.6)
      ..style = PaintingStyle.fill;

    canvas.drawPath(path, arrowPaint);
  }

  void _drawNode(Canvas canvas, MindMapNode node) {
    final textColor = brightness == Brightness.dark ? Colors.white : Colors.black87;
    final isRoot = node.level == 0;

    final textPainter = TextPainter(
      text: TextSpan(
        text: node.label,
        style: TextStyle(
          color: textColor,
          fontSize: isRoot ? 20 : 16,
          fontWeight: isRoot ? FontWeight.bold : FontWeight.w600,
        ),
      ),
      textDirection: TextDirection.ltr,
      maxLines: 2,
    );
    textPainter.layout(maxWidth: 140);

    final padding = isRoot ? 20.0 : 16.0;
    final boxWidth = textPainter.width + padding * 2;
    final boxHeight = textPainter.height + padding * 1.5;

    // 绘制阴影
    if (brightness == Brightness.light) {
      final shadowRect = RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: node.position.translate(3, 3),
          width: boxWidth,
          height: boxHeight,
        ),
        const Radius.circular(12),
      );
      final shadowPaint = Paint()
        ..color = Colors.black.withOpacity(0.1)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6);
      canvas.drawRRect(shadowRect, shadowPaint);
    }

    // 绘制节点背景
    final rect = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: node.position,
        width: boxWidth,
        height: boxHeight,
      ),
      const Radius.circular(12),
    );

    final nodeColor = _getNodeColor(node);
    final bgColor = brightness == Brightness.dark
        ? nodeColor
        : Color.lerp(nodeColor, Colors.white, 0.85)!;

    final boxPaint = Paint()
      ..color = bgColor
      ..style = PaintingStyle.fill;

    canvas.drawRRect(rect, boxPaint);

    // 绘制边框
    final borderColor = brightness == Brightness.dark
        ? nodeColor.withOpacity(0.8)
        : nodeColor.withOpacity(0.6);

    final borderPaint = Paint()
      ..color = borderColor
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke;

    canvas.drawRRect(rect, borderPaint);

    // 如果不是根节点，添加情感标签
    if (!isRoot) {
      _drawSentimentBadge(canvas, node, rect, nodeColor);
    }

    // 绘制文本
    textPainter.paint(
      canvas,
      Offset(
        node.position.dx - textPainter.width / 2,
        node.position.dy - textPainter.height / 2,
      ),
    );
  }

  void _drawSentimentBadge(Canvas canvas, MindMapNode node, RRect rect, Color color) {
    final badgeSize = 24.0;
    final badgePos = Offset(
      rect.right - badgeSize / 2 - 8,
      rect.top + badgeSize / 2 + 8,
    );

    // 绘制圆形背景
    final badgePaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    canvas.drawCircle(badgePos, badgeSize / 2, badgePaint);

    // 绘制图标
    final iconPainter = TextPainter(
      text: TextSpan(
        text: _getSentimentIcon(node),
        style: const TextStyle(
          fontSize: 14,
          color: Colors.white,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    iconPainter.layout();
    iconPainter.paint(
      canvas,
      Offset(
        badgePos.dx - iconPainter.width / 2,
        badgePos.dy - iconPainter.height / 2,
      ),
    );
  }

  String _getSentimentIcon(MindMapNode node) {
    // 根据节点位置或内容判断情感（这里简化处理）
    final hash = node.label.hashCode % 3;
    if (sentimentScore >= 60) {
      return hash == 0 ? '😊' : (hash == 1 ? '👍' : '✓');
    } else if (sentimentScore < 40) {
      return hash == 0 ? '😟' : (hash == 1 ? '👎' : '✗');
    } else {
      return hash == 0 ? '😐' : (hash == 1 ? '➖' : '○');
    }
  }

  Color _getNodeColor(MindMapNode node) {
    if (node.level == 0) {
      // 根节点使用主色调
      return const Color(0xFF5E35B1);
    }

    // 子节点根据情感得分着色
    if (sentimentScore >= 60) {
      return const Color(0xFF43A047); // 绿色 - 正面
    } else if (sentimentScore < 40) {
      return const Color(0xFFE53935); // 红色 - 负面
    } else {
      return const Color(0xFFFFA726); // 橙黄色 - 中性
    }
  }

  @override
  bool shouldRepaint(SentimentMindMapPainter oldDelegate) => false;
}
