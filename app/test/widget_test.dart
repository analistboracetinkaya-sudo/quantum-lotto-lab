import 'package:flutter_test/flutter_test.dart';

import 'package:kuponiq_quantum/main.dart';

void main() {
  testWidgets('KuponIQ shell renders primary screens', (tester) async {
    await tester.pumpWidget(const KuponIqApp());

    expect(find.text('KuponIQ Quantum'), findsWidgets);
    expect(find.text('Rastgeleliği ölç. Kuponu hazırla.'), findsOneWidget);

    await tester.tap(find.text('Lotolar'));
    await tester.pumpAndSettle();

    expect(find.text('Loto seç'), findsOneWidget);
    expect(find.text('Süper Loto'), findsOneWidget);
  });
}
