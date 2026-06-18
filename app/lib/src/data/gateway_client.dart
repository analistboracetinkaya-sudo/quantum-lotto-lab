import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models.dart';

class GatewayClient {
  GatewayClient({String? baseUrl})
    : baseUrl = Uri.parse(baseUrl ?? 'http://127.0.0.1:8787');

  final Uri baseUrl;

  Future<bool> health() async {
    final response = await http
        .get(baseUrl.resolve('/health'))
        .timeout(const Duration(seconds: 2));
    if (response.statusCode != 200) {
      return false;
    }
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return json['ok'] == true;
  }

  Future<List<LotteryGame>> lotteries() async {
    final response = await http
        .get(baseUrl.resolve('/lotteries'))
        .timeout(const Duration(seconds: 4));
    if (response.statusCode != 200) {
      return const [];
    }
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    final games = json['games'] as List<dynamic>? ?? const [];
    return games
        .whereType<Map<String, dynamic>>()
        .map(LotteryGame.fromJson)
        .toList();
  }

  Future<DataHealth> dataHealth(String slug) async {
    final response = await http
        .get(baseUrl.resolve('/lotteries/$slug/data-health'))
        .timeout(const Duration(seconds: 4));
    if (response.statusCode != 200) {
      throw StateError('Gateway returned ${response.statusCode}.');
    }
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return DataHealth.fromJson(json);
  }

  Future<QuantumStatus> ibmStatus() async {
    final response = await http
        .get(baseUrl.resolve('/ibm/status'))
        .timeout(const Duration(seconds: 8));
    if (response.statusCode != 200) {
      throw StateError('Gateway returned ${response.statusCode}.');
    }
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return QuantumStatus.fromJson(json);
  }

  Future<QuantumStatus> saveIbmToken(String token) async {
    final response = await http
        .post(
          baseUrl.resolve('/ibm/token'),
          headers: const {'content-type': 'application/json'},
          body: jsonEncode({'token': token}),
        )
        .timeout(const Duration(seconds: 12));
    if (response.statusCode != 200) {
      throw StateError('Gateway returned ${response.statusCode}.');
    }
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return QuantumStatus.fromJson(json);
  }
}
