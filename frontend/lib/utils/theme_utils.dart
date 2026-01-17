import 'package:flutter/material.dart';

class ThemeUtils {
  // 获取卡片背景色
  static Color getCardColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return isDark ? const Color(0xFF232629) : Colors.white;
  }

  // 获取卡片边框色
  static Color getCardBorderColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return isDark 
        ? Colors.white.withOpacity(0.08)
        : Colors.black.withOpacity(0.08);
  }

  // 获取次要文字颜色
  static Color getSecondaryTextColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return isDark 
        ? Colors.white.withOpacity(0.6)
        : Colors.black.withOpacity(0.6);
  }

  // 获取禁用文字颜色
  static Color getDisabledTextColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return isDark 
        ? Colors.white.withOpacity(0.4)
        : Colors.black.withOpacity(0.4);
  }

  // 获取卡片阴影
  static List<BoxShadow>? getCardShadow(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    if (isDark) return null;
    return [
      BoxShadow(
        color: Colors.black.withOpacity(0.05),
        blurRadius: 8,
        offset: const Offset(0, 2),
      ),
    ];
  }

  // 获取分隔线颜色
  static Color getDividerColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return isDark 
        ? Colors.white.withOpacity(0.1)
        : Colors.black.withOpacity(0.1);
  }
}
