import '../models.dart';

class DemoRepository {
  final List<LotteryGame> games = const [
    LotteryGame(
      slug: 'super-loto-tr',
      name: 'Süper Loto',
      drawKind: '6/60',
      rows: 1135,
      status: 'public_archive',
      modelStatus: 'ready',
      datedHistoryReady: true,
    ),
    LotteryGame(
      slug: 'cilgin-sayisal-loto-tr',
      name: 'Çılgın Sayısal Loto',
      drawKind: '6/90 + Joker',
      rows: 1236,
      status: 'public_archive',
      modelStatus: 'ready',
      datedHistoryReady: true,
    ),
    LotteryGame(
      slug: 'sans-topu-tr',
      name: 'Şans Topu',
      drawKind: '5/34 + 1/14',
      rows: 816,
      status: 'public_archive',
      modelStatus: 'ready',
      datedHistoryReady: true,
    ),
    LotteryGame(
      slug: 'on-numara-tr',
      name: 'On Numara',
      drawKind: '22/80 draw, 10/80 kupon',
      rows: 779,
      status: 'public_archive_missing_dates',
      modelStatus: 'audit_ready_coupon_adapter',
      datedHistoryReady: false,
    ),
    LotteryGame(
      slug: 'hizli-on-numara-tr',
      name: 'Hızlı On',
      drawKind: '1-10/80',
      rows: 0,
      status: 'no_10y_archive_new_game',
      modelStatus: 'adapter_ready_limited_archive',
      datedHistoryReady: false,
    ),
  ];

  final DataHealth dataHealth = const DataHealth(
    ready: true,
    rows: 1135,
    firstDraw: '2016-06-23',
    lastDraw: '2026-06-16',
    issue: null,
  );

  DataHealth healthFor(String slug) {
    if (slug == 'on-numara-tr') {
      return const DataHealth(
        ready: false,
        rows: 779,
        firstDraw: null,
        lastDraw: null,
        issue: 'Kaynak yıllı/çekiliş numaralı; tam tarih yok.',
      );
    }
    final game = games.firstWhere(
      (item) => item.slug == slug,
      orElse: () => games.first,
    );
    return DataHealth(
      ready: game.datedHistoryReady,
      rows: game.rows,
      firstDraw: game.datedHistoryReady ? '2016-06-18' : null,
      lastDraw: game.datedHistoryReady ? '2026-06-17' : null,
      issue: game.datedHistoryReady ? null : 'Dated archive bekliyor.',
    );
  }

  final CouponPortfolio portfolio = const CouponPortfolio(
    columns: 30,
    unionCoverage: 60,
    anyTwoPlus: .9769,
    anyThreePlus: .5269,
    tickets: [
      CouponTicket(main: [7, 14, 37, 41, 43, 51]),
      CouponTicket(main: [11, 15, 17, 18, 34, 60]),
      CouponTicket(main: [2, 3, 16, 36, 48, 56]),
      CouponTicket(main: [6, 8, 20, 32, 47, 52]),
      CouponTicket(main: [21, 27, 29, 31, 42, 45]),
    ],
  );

  final QuantumStatus quantumStatus = const QuantumStatus(
    connected: false,
    message: 'Gateway bağlı değil; IBM durumu demo modda.',
    backends: [
      QuantumBackend(name: 'ibm_kingston', qubits: 127),
      QuantumBackend(name: 'ibm_marrakesh', qubits: 156),
    ],
  );
}
