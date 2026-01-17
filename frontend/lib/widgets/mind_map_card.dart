import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart' as wf;

class MindMapCard extends StatefulWidget {
  final String mermaidCode;
  const MindMapCard({Key? key, required this.mermaidCode}) : super(key: key);

  @override
  State<MindMapCard> createState() => _MindMapCardState();
}

class _MindMapCardState extends State<MindMapCard> {
  wf.WebViewController? _controller;

  @override
  void initState() {
    super.initState();
    if (!kIsWeb) {
      _initController();
    }
  }

  void _initController() {
    _controller = wf.WebViewController()
      ..setJavaScriptMode(wf.JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0x00000000))
      ..loadHtmlString(_getHtml(widget.mermaidCode));
  }

  @override
  void didUpdateWidget(MindMapCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.mermaidCode != widget.mermaidCode && _controller != null) {
      _controller?.loadHtmlString(_getHtml(widget.mermaidCode));
    }
  }

  String _getHtml(String code) {
    if (code.isEmpty) return '';
    return '''
<!DOCTYPE html>
<html>
<head>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true, theme: 'dark' });
  </script>
  <style>
    body { 
      background-color: #232629; 
      color: white; 
      margin: 0; 
      display: flex; 
      justify-content: center; 
      align-items: center; 
      height: 100vh; 
      overflow: hidden; 
    }
  </style>
</head>
<body>
  <div class="mermaid">
    $code
  </div>
</body>
</html>
    ''';
  }

  @override
  Widget build(BuildContext context) {
    Widget content;
    
    if (widget.mermaidCode.isEmpty) {
      content = const Center(child: Text('暂无思维导图数据'));
    } else if (kIsWeb) {
      // Web 平台：显示原始 Mermaid 代码或提示
      content = SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.info_outline, size: 20, color: Colors.blue),
                SizedBox(width: 8),
                Text(
                  'Mermaid 思维导图代码',
                  style: TextStyle(
                    color: Colors.blue,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black26,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white24),
              ),
              child: SelectableText(
                widget.mermaidCode,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: Colors.white70,
                ),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              '💡 提示：复制代码到 mermaid.live 查看可视化图表',
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      );
    } else if (_controller != null) {
      content = wf.WebViewWidget(controller: _controller!);
    } else {
      content = const Center(child: CircularProgressIndicator());
    }

    return Card(
      child: Container(
        height: 300,
        padding: const EdgeInsets.all(8),
        child: content,
      ),
    );
  }
}
