import 'package:flutter_test/flutter_test.dart';

import 'package:kuponiq_quantum/src/app.dart';

void main() {
  testWidgets('KuponIQ shell renders primary screens', (tester) async {
    await tester.pumpWidget(const KuponIqQuantumApp());
    await tester.pump();

    expect(find.text('KuponIQ'), findsWidgets);
    expect(find.text('KuponIQ Quantum'), findsOneWidget);

    await tester.tap(find.text('Loto'));
    await tester.pump(const Duration(milliseconds: 320));

    expect(find.text('Loto seç'), findsOneWidget);
    expect(find.text('Süper Loto'), findsWidgets);

    await tester.tap(find.text('Analiz'));
    await tester.pump(const Duration(milliseconds: 320));

    expect(find.text('Analiz merkezi'), findsOneWidget);
  });
}
