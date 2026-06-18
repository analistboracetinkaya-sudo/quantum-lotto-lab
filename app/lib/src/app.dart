import 'package:flutter/material.dart';

import 'app_controller.dart';
import 'data/demo_repository.dart';
import 'data/gateway_client.dart';
import 'screens/app_shell.dart';

class KuponIqQuantumApp extends StatefulWidget {
  const KuponIqQuantumApp({super.key});

  @override
  State<KuponIqQuantumApp> createState() => _KuponIqQuantumAppState();
}

class _KuponIqQuantumAppState extends State<KuponIqQuantumApp> {
  late final AppController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AppController(
      demoRepository: DemoRepository(),
      gatewayClient: GatewayClient(),
    )..boot();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return KuponIqScope(
      controller: _controller,
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'KuponIQ Quantum',
        theme: _theme(),
        home: const AppShell(),
      ),
    );
  }
}

class KuponIqScope extends InheritedNotifier<AppController> {
  const KuponIqScope({
    super.key,
    required AppController controller,
    required super.child,
  }) : super(notifier: controller);

  static AppController of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<KuponIqScope>();
    assert(scope != null, 'KuponIqScope is missing.');
    return scope!.notifier!;
  }
}

ThemeData _theme() {
  const seed = Color(0xFF18B7A0);
  const surface = Color(0xFF071A1D);
  const ink = Color(0xFFE9FFFA);

  return ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: seed,
      brightness: Brightness.dark,
    ),
    scaffoldBackgroundColor: surface,
    useMaterial3: true,
    textTheme: const TextTheme(
      headlineSmall: TextStyle(fontWeight: FontWeight.w800, color: ink),
      titleLarge: TextStyle(fontWeight: FontWeight.w800, color: ink),
      titleMedium: TextStyle(fontWeight: FontWeight.w700, color: ink),
      bodyMedium: TextStyle(height: 1.35, color: Color(0xFFB5CBC7)),
      labelMedium: TextStyle(color: Color(0xFF8FB3AE)),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: surface,
      foregroundColor: ink,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: const Color(0xFF10272B),
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: Color(0xFF244246)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      filled: true,
      fillColor: const Color(0xFF10272B),
    ),
  );
}
