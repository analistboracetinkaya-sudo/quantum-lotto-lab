class LotteryGame {
  const LotteryGame({
    required this.slug,
    required this.name,
    required this.drawKind,
    required this.rows,
    required this.status,
    required this.modelStatus,
    required this.datedHistoryReady,
  });

  factory LotteryGame.fromJson(Map<String, dynamic> json) => LotteryGame(
    slug: json['slug'] as String? ?? '',
    name: json['name'] as String? ?? '',
    drawKind: json['draw_kind'] as String? ?? json['rule'] as String? ?? '',
    rows: _intValue(json['rows']),
    status: json['data_status'] as String? ?? 'unknown',
    modelStatus: json['model_status'] as String? ?? 'ready',
    datedHistoryReady: json['dated_history_ready'] as bool? ?? false,
  );

  final String slug;
  final String name;
  final String drawKind;
  final int rows;
  final String status;
  final String modelStatus;
  final bool datedHistoryReady;

  String get displayStatus {
    if (datedHistoryReady) {
      return 'Veri hazır';
    }
    if (rows > 0) {
      return 'Veri sınırlı';
    }
    return 'Adapter hazır';
  }
}

class DataHealth {
  const DataHealth({
    required this.ready,
    required this.rows,
    required this.firstDraw,
    required this.lastDraw,
    required this.issue,
  });

  factory DataHealth.fromJson(Map<String, dynamic> json) => DataHealth(
    ready: json['ready'] as bool? ?? false,
    rows: _intValue(json['rows']),
    firstDraw: json['first_draw'] as String?,
    lastDraw: json['last_draw'] as String?,
    issue: json['issue'] as String?,
  );

  final bool ready;
  final int rows;
  final String? firstDraw;
  final String? lastDraw;
  final String? issue;
}

class CouponTicket {
  const CouponTicket({required this.main, this.bonus = const []});

  factory CouponTicket.fromJson(Map<String, dynamic> json) => CouponTicket(
    main: _intList(json['main']),
    bonus: _intList(json['bonus']),
  );

  final List<int> main;
  final List<int> bonus;
}

class CouponPortfolio {
  const CouponPortfolio({
    required this.columns,
    required this.unionCoverage,
    required this.anyTwoPlus,
    required this.anyThreePlus,
    required this.tickets,
  });

  final int columns;
  final int unionCoverage;
  final double anyTwoPlus;
  final double anyThreePlus;
  final List<CouponTicket> tickets;
}

class QuantumBackend {
  const QuantumBackend({required this.name, required this.qubits});

  factory QuantumBackend.fromJson(Map<String, dynamic> json) => QuantumBackend(
    name: json['name'] as String? ?? '',
    qubits: _intValue(json['num_qubits']),
  );

  final String name;
  final int qubits;
}

class QuantumStatus {
  const QuantumStatus({
    required this.connected,
    required this.message,
    required this.backends,
  });

  factory QuantumStatus.fromJson(Map<String, dynamic> json) {
    final rawBackends = json['backends'] as List<dynamic>? ?? const [];
    return QuantumStatus(
      connected: json['connected'] as bool? ?? false,
      message: json['message'] as String? ?? '',
      backends: rawBackends
          .whereType<Map<String, dynamic>>()
          .map(QuantumBackend.fromJson)
          .toList(),
    );
  }

  final bool connected;
  final String message;
  final List<QuantumBackend> backends;
}

int _intValue(Object? value) {
  if (value is int) {
    return value;
  }
  if (value is num) {
    return value.toInt();
  }
  return int.tryParse(value?.toString() ?? '') ?? 0;
}

List<int> _intList(Object? value) {
  if (value is List) {
    return value
        .map((item) => _intValue(item))
        .where((item) => item > 0)
        .toList();
  }
  return const [];
}
