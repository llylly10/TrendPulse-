import 'package:flutter/material.dart';
import 'dart:math' as math;

class FlutterMindMap extends StatelessWidget {
  final String mermaidCode;
  final double sentimentScore; // 添加情感得分参数

  const FlutterMindMap({
    Key? key, 
    required this.mermaidCode,
    this.sentimentScore = 50.0, // 默认中性
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

    // 获取当前主题的亮度
    final brightness = Theme.of(context).brightness;

    return InteractiveViewer(
      boundaryMargin: const EdgeInsets.all(50),
      minScale: 0.5,
      maxScale: 2.0,
      child: CustomPaint(
        size: const Size(800, 600),
        painter: MindMapPainter(nodes, sentimentScore, brightness),
      ),
    );
  }

  List<MindMapNode> _parseMermaidCode(String code) {
    final nodes = <MindMapNode>[];
    final connections = <MapConnection>[];
    final nodeMap = <String, MindMapNode>{};

    // 解析 Mermaid 代码
    // 格式: graph TD; A[文本] --> B[文本2]; A --> C[文本3];
    final lines = code.split(';');
    
    for (var line in lines) {
      line = line.trim();
      if (line.isEmpty || line.startsWith('graph')) continue;

      // 匹配箭头连接: A --> B 或 A[文本] --> B[文本2]
      final arrowMatch = RegExp(r'(\w+)(?:\[([^\]]+)\])?\s*-->\s*(\w+)(?:\[([^\]]+)\])?').firstMatch(line);
      
      if (arrowMatch != null) {
        final fromId = arrowMatch.group(1)!;
        final fromLabel = arrowMatch.group(2) ?? fromId;
        final toId = arrowMatch.group(3)!;
        final toLabel = arrowMatch.group(4) ?? toId;

        // 创建或获取节点
        if (!nodeMap.containsKey(fromId)) {
          nodeMap[fromId] = MindMapNode(id: fromId, label: fromLabel);
        }
        if (!nodeMap.containsKey(toId)) {
          nodeMap[toId] = MindMapNode(id: toId, label: toLabel);
        }

        // 添加连接
        connections.add(MapConnection(from: fromId, to: toId));
      }
    }

    // 构建树结构
    if (nodeMap.isEmpty) return [];

    // 找到根节点（没有父节点的节点）
    final childIds = connections.map((c) => c.to).toSet();
    final rootId = nodeMap.keys.firstWhere(
      (id) => !childIds.contains(id),
      orElse: () => nodeMap.keys.first,
    );

    // 计算节点位置
    _calculatePositions(nodeMap, connections, rootId);

    return nodeMap.values.toList();
  }

  void _calculatePositions(
    Map<String, MindMapNode> nodeMap,
    List<MapConnection> connections,
    String rootId,
  ) {
    final root = nodeMap[rootId]!;
    root.position = const Offset(400, 80);
    root.level = 0;

    // 保存连接信息
    for (var conn in connections) {
      final from = nodeMap[conn.from];
      final to = nodeMap[conn.to];
      if (from != null && to != null) {
        from.children.add(to);
      }
    }

    // BFS 遍历计算位置
    final queue = <String>[rootId];
    final visited = <String>{rootId};

    while (queue.isNotEmpty) {
      final currentId = queue.removeAt(0);
      final current = nodeMap[currentId]!;

      // 找到所有子节点
      final children = connections
          .where((c) => c.from == currentId)
          .map((c) => c.to)
          .where((id) => !visited.contains(id))
          .toList();

      if (children.isEmpty) continue;

      // 计算子节点位置 - 更大的间距
      final childLevel = current.level + 1;
      final yOffset = 120.0; // 增加垂直间距
      final xSpacing = math.max(180.0, 600.0 / children.length); // 动态水平间距
      final totalWidth = (children.length - 1) * xSpacing;
      final startX = current.position.dx - totalWidth / 2;

      for (var i = 0; i < children.length; i++) {
        final childId = children[i];
        final child = nodeMap[childId]!;
        child.level = childLevel;
        child.position = Offset(
          startX + i * xSpacing,
          current.position.dy + yOffset,
        );
        child.parent = currentId;
        
        visited.add(childId);
        queue.add(childId);
      }
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

class MindMapPainter extends CustomPainter {
  final List<MindMapNode> nodes;
  final double sentimentScore;
  final Brightness brightness;

  MindMapPainter(this.nodes, this.sentimentScore, this.brightness);

  @override
  void paint(Canvas canvas, Size size) {
    // 根据情感得分选择颜色主题
    final Color lineColor = _getLineColor();
    
    // 绘制连接线
    final linePaint = Paint()
      ..color = lineColor.withOpacity(0.6)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke;

    // 绘制箭头
    final arrowPaint = Paint()
      ..color = lineColor.withOpacity(0.6)
      ..style = PaintingStyle.fill;

    for (var node in nodes) {
      for (var child in node.children) {
        final path = Path();
        path.moveTo(node.position.dx, node.position.dy + 25);
        
        // 绘制贝塞尔曲线
        final controlPoint1 = Offset(
          node.position.dx,
          node.position.dy + (child.position.dy - node.position.dy) / 2,
        );
        final controlPoint2 = Offset(
          child.position.dx,
          node.position.dy + (child.position.dy - node.position.dy) / 2,
        );
        
        path.cubicTo(
          controlPoint1.dx, controlPoint1.dy,
          controlPoint2.dx, controlPoint2.dy,
          child.position.dx, child.position.dy - 25,
        );
        
        canvas.drawPath(path, linePaint);

        // 绘制箭头
        _drawArrow(canvas, arrowPaint, child.position.dx, child.position.dy - 25);
      }
    }

    // 绘制节点
    for (var node in nodes) {
      _drawNode(canvas, node);
    }
  }

  void _drawArrow(Canvas canvas, Paint paint, double x, double y) {
    final path = Path();
    path.moveTo(x, y);
    path.lineTo(x - 6, y - 10);
    path.lineTo(x + 6, y - 10);
    path.close();
    canvas.drawPath(path, paint);
  }

  void _drawNode(Canvas canvas, MindMapNode node) {
    // 根据主题亮度选择文字颜色
    final textColor = brightness == Brightness.dark ? Colors.white : Colors.black87;
    
    final textPainter = TextPainter(
      text: TextSpan(
        text: node.label,
        style: TextStyle(
          color: textColor,
          fontSize: node.level == 0 ? 18 : 15,
          fontWeight: node.level == 0 ? FontWeight.bold : FontWeight.w500,
        ),
      ),
      textDirection: TextDirection.ltr,
      maxLines: 2,
    );
    textPainter.layout(maxWidth: 150);

    final padding = node.level == 0 ? 16.0 : 14.0;
    final boxWidth = textPainter.width + padding * 2;
    final boxHeight = textPainter.height + padding * 1.2;

    // 绘制阴影
    final shadowRect = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: node.position.translate(2, 2),
        width: boxWidth,
        height: boxHeight,
      ),
      const Radius.circular(10),
    );
    final shadowPaint = Paint()
      ..color = Colors.black.withOpacity(brightness == Brightness.dark ? 0.3 : 0.15)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);
    canvas.drawRRect(shadowRect, shadowPaint);

    // 绘制节点背景
    final rect = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: node.position,
        width: boxWidth,
        height: boxHeight,
      ),
      const Radius.circular(10),
    );

    // 根据主题调整背景颜色
    final gradientColors = _getNodeGradient(node.level);
    final adjustedColors = brightness == Brightness.dark 
        ? gradientColors 
        : gradientColors.map((c) => Color.lerp(c, Colors.white, 0.7)!).toList();

    final boxPaint = Paint()
      ..shader = LinearGradient(
        colors: adjustedColors,
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(rect.outerRect)
      ..style = PaintingStyle.fill;

    canvas.drawRRect(rect, boxPaint);

    // 绘制边框 - 根据主题调整边框颜色
    final borderColor = brightness == Brightness.dark 
        ? Colors.white.withOpacity(0.4)
        : Colors.black.withOpacity(0.3);
    
    final borderPaint = Paint()
      ..color = borderColor
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    canvas.drawRRect(rect, borderPaint);

    // 绘制文本
    textPainter.paint(
      canvas,
      Offset(
        node.position.dx - textPainter.width / 2,
        node.position.dy - textPainter.height / 2,
      ),
    );
  }

  List<Color> _getNodeGradient(int level) {
    // 根据情感得分返回不同颜色
    if (sentimentScore >= 60) {
      // 正面：绿色系
      final gradients = [
        [const Color(0xFF2E7D32), const Color(0xFF43A047)], // 深绿
        [const Color(0xFF388E3C), const Color(0xFF66BB6A)], // 中绿
        [const Color(0xFF4CAF50), const Color(0xFF81C784)], // 浅绿
        [const Color(0xFF66BB6A), const Color(0xFFA5D6A7)], // 更浅绿
      ];
      return gradients[level % gradients.length];
    } else if (sentimentScore < 40) {
      // 负面：红色系
      final gradients = [
        [const Color(0xFFC62828), const Color(0xFFE53935)], // 深红
        [const Color(0xFFD32F2F), const Color(0xFFEF5350)], // 中红
        [const Color(0xFFE53935), const Color(0xFFEF5350)], // 浅红
        [const Color(0xFFEF5350), const Color(0xFFE57373)], // 更浅红
      ];
      return gradients[level % gradients.length];
    } else {
      // 中性：蓝色系
      final gradients = [
        [const Color(0xFF1565C0), const Color(0xFF1976D2)], // 深蓝
        [const Color(0xFF1976D2), const Color(0xFF42A5F5)], // 中蓝
        [const Color(0xFF2196F3), const Color(0xFF64B5F6)], // 浅蓝
        [const Color(0xFF42A5F5), const Color(0xFF90CAF9)], // 更浅蓝
      ];
      return gradients[level % gradients.length];
    }
  }

  Color _getLineColor() {
    if (sentimentScore >= 60) {
      return const Color(0xFF43A047); // 绿色
    } else if (sentimentScore < 40) {
      return const Color(0xFFE53935); // 红色
    } else {
      return const Color(0xFF1976D2); // 蓝色
    }
  }

  @override
  bool shouldRepaint(MindMapPainter oldDelegate) => false;
}
