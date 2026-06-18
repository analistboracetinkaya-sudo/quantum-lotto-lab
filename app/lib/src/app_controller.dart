import 'dart:async';

import 'package:flutter/foundation.dart';

import 'data/demo_repository.dart';
import 'data/gateway_client.dart';
import 'models.dart';

class AppController extends ChangeNotifier {
  AppController({required this.demoRepository, required this.gatewayClient})
    : games = demoRepository.games,
      selectedGame = demoRepository.games.first,
      dataHealth = demoRepository.dataHealth,
      portfolio = demoRepository.portfolio,
      quantumStatus = demoRepository.quantumStatus;

  final DemoRepository demoRepository;
  final GatewayClient gatewayClient;

  List<LotteryGame> games;
  LotteryGame selectedGame;
  DataHealth dataHealth;
  CouponPortfolio portfolio;
  QuantumStatus quantumStatus;
  bool gatewayOnline = false;
  bool loading = true;
  int screenIndex = 0;
  String statusMessage = 'Demo mod hazır.';
  String ibmTokenInput = '';

  Future<void> boot() async {
    loading = true;
    notifyListeners();
    try {
      gatewayOnline = await gatewayClient.health();
      final remoteGames = await gatewayClient.lotteries();
      if (remoteGames.isNotEmpty) {
        games = remoteGames;
        selectedGame = games.firstWhere(
          (game) => game.slug == selectedGame.slug,
          orElse: () => games.first,
        );
      }
      await refreshDataHealth();
      statusMessage = gatewayOnline
          ? 'Yerel Quantum Gateway bağlı.'
          : 'Gateway kapalı; demo verisi kullanılıyor.';
      unawaited(refreshQuantumStatus());
    } catch (error) {
      gatewayOnline = false;
      statusMessage = 'Gateway kapalı; demo verisi kullanılıyor.';
    } finally {
      loading = false;
      notifyListeners();
    }
  }

  void setScreen(int index) {
    screenIndex = index;
    notifyListeners();
  }

  Future<void> selectGame(LotteryGame game) async {
    selectedGame = game;
    dataHealth = demoRepository.healthFor(game.slug);
    notifyListeners();
    await refreshDataHealth();
  }

  Future<void> refreshDataHealth() async {
    if (!gatewayOnline) {
      dataHealth = demoRepository.healthFor(selectedGame.slug);
      notifyListeners();
      return;
    }
    try {
      dataHealth = await gatewayClient.dataHealth(selectedGame.slug);
    } catch (_) {
      dataHealth = demoRepository.healthFor(selectedGame.slug);
    }
    notifyListeners();
  }

  Future<void> refreshQuantumStatus() async {
    if (!gatewayOnline) {
      quantumStatus = demoRepository.quantumStatus;
      notifyListeners();
      return;
    }
    try {
      quantumStatus = await gatewayClient.ibmStatus();
    } catch (error) {
      quantumStatus = QuantumStatus(
        connected: false,
        message: error.toString(),
        backends: const [],
      );
    }
    notifyListeners();
  }

  void setIbmTokenInput(String value) {
    ibmTokenInput = value.trim();
  }

  Future<void> saveIbmToken() async {
    if (ibmTokenInput.isEmpty) {
      statusMessage = 'IBM token boş olamaz.';
      notifyListeners();
      return;
    }
    if (!gatewayOnline) {
      statusMessage = 'Token kaydı için yerel gateway çalışmalı.';
      notifyListeners();
      return;
    }
    try {
      quantumStatus = await gatewayClient.saveIbmToken(ibmTokenInput);
      ibmTokenInput = '';
      statusMessage = quantumStatus.connected
          ? 'IBM token lokal Qiskit hesabına kaydedildi.'
          : 'Token kaydedildi; IBM bağlantısı doğrulanamadı.';
    } catch (error) {
      statusMessage = 'IBM token kaydedilemedi: $error';
    }
    notifyListeners();
  }
}
