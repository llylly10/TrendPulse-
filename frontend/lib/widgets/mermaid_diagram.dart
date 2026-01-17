import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart' as wf;
import 'package:webview_windows/webview_windows.dart' as win;

class MermaidDiagram extends StatefulWidget {
  final String code;
  final double height;

  const MermaidDiagram({
    Key? key,
    required this.code,
    this.height = 300,
  }) : super(key: key);

  @override
  State<MermaidDiagram> createState() => _MermaidDiagramState();
}

class _MermaidDiagramState extends State<MermaidDiagram> {
  // Mobile/Web controller
  wf.WebViewController? _mobileController;
  // Windows controller
  win.WebviewController? _windowsController;

  bool _isWindowsInitialized = false;

  @override
  void initState() {
    super.initState();
    if (!kIsWeb && Platform.isWindows) {
      _initWindows();
    } else {
      _initMobile();
    }
  }

  void _initMobile() {
    _mobileController = wf.WebViewController()
      ..setJavaScriptMode(wf.JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0x00000000))
      ..loadHtmlString(_getHtml(widget.code));
  }

  Future<void> _initWindows() async {
    _windowsController = win.WebviewController();
    try {
      await _windowsController!.initialize();
      await _windowsController!.loadStringContent(_getHtml(widget.code));
      if (mounted) {
        setState(() {
          _isWindowsInitialized = true;
        });
      }
    } catch (e) {
      print('Error initializing Windows WebView: $e');
    }
  }

  @override
  void didUpdateWidget(MermaidDiagram oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.code != widget.code) {
      if (!kIsWeb && Platform.isWindows && _isWindowsInitialized) {
        _windowsController?.loadStringContent(_getHtml(widget.code));
      } else if (_mobileController != null) {
        _mobileController?.loadHtmlString(_getHtml(widget.code));
      }
    }
  }

  @override
  void dispose() {
    _windowsController?.dispose();
    super.dispose();
  }

  String _getHtml(String code) {
    if (code.isEmpty) return '';
    return '''
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ 
      startOnLoad: true, 
      theme: 'dark',
      securityLevel: 'loose',
    });
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
      font-family: sans-serif;
    }
    .mermaid {
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
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
    if (widget.code.isEmpty) {
      return Container(
        height: widget.height,
        alignment: Alignment.center,
        child: const Text('暂无思维导图数据', style: TextStyle(color: Colors.white54)),
      );
    }

    Widget content;
    if (!kIsWeb && Platform.isWindows) {
      if (!_isWindowsInitialized) {
        content = const Center(child: CircularProgressIndicator());
      } else {
        content = win.Webview(_windowsController!);
      }
    } else {
      // Mobile & Web
      content = wf.WebViewWidget(controller: _mobileController!);
    }

    return SizedBox(
      height: widget.height,
      child: content,
    );
  }
}
