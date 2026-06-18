import 'package:flutter/material.dart';

import '../app.dart';
import '../app_controller.dart';
import '../widgets/ui.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell>
    with SingleTickerProviderStateMixin {
  late final AnimationController _motion;

  static const _destinations = [
    _Destination('Ana', Icons.auto_awesome),
    _Destination('Loto', Icons.casino_outlined),
    _Destination('Analiz', Icons.analytics_outlined),
    _Destination('Kupon', Icons.confirmation_number_outlined),
    _Destination('Ayarlar', Icons.settings_outlined),
  ];

  @override
  void initState() {
    super.initState();
    _motion = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat();
  }

  @override
  void dispose() {
    _motion.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = KuponIqScope.of(context);
    return AnimatedBuilder(
      animation: Listenable.merge([controller, _motion]),
      builder: (context, _) {
        final pages = [
          OverviewScreen(controller: controller, motion: _motion.value),
          LotteryScreen(controller: controller),
          AnalysisWorkspaceScreen(controller: controller),
          CouponWorkspaceScreen(controller: controller),
          SettingsWorkspaceScreen(controller: controller),
        ];
        return Scaffold(
          extendBody: true,
          body: Stack(
            children: [
              PremiumBackdrop(progress: _motion.value),
              SafeArea(
                bottom: false,
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 10, 18, 0),
                      child: PremiumTopBar(
                        gatewayOnline: controller.gatewayOnline,
                        onRefresh: controller.boot,
                      ),
                    ),
                    Expanded(
                      child: AnimatedSwitcher(
                        duration: const Duration(milliseconds: 260),
                        switchInCurve: Curves.easeOutCubic,
                        switchOutCurve: Curves.easeOutCubic,
                        child: KeyedSubtree(
                          key: ValueKey(controller.screenIndex),
                          child: pages[controller.screenIndex],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          bottomNavigationBar: FloatingNavBar(
            items: _destinations
                .map((item) => (item.label, item.icon))
                .toList(),
            selectedIndex: controller.screenIndex,
            onSelected: controller.setScreen,
          ),
        );
      },
    );
  }
}

class OverviewScreen extends StatelessWidget {
  const OverviewScreen({
    super.key,
    required this.controller,
    required this.motion,
  });

  final AppController controller;
  final double motion;

  @override
  Widget build(BuildContext context) {
    return AppFrame(
      child: ListView(
        physics: const BouncingScrollPhysics(),
        padding: EdgeInsets.zero,
        children: [
          QuantumHeroCard(progress: motion),
          const SizedBox(height: 18),
          Row(
            children: [
              Expanded(
                child: Text(
                  controller.selectedGame.name,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              StatusPill(
                label: controller.gatewayOnline ? 'Canlı' : 'Demo',
                tone: controller.gatewayOnline ? PillTone.good : PillTone.warn,
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${controller.selectedGame.drawKind} · ${controller.statusMessage}',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 18),
          MetricGrid(
            metrics: [
              MetricItem('Arşiv', '${controller.dataHealth.rows}', .78),
              MetricItem('Kolon', '${controller.portfolio.columns}', .30),
              MetricItem(
                'Kapsama',
                '${controller.portfolio.unionCoverage}/60',
                1,
              ),
              MetricItem(
                'IBM QPU',
                controller.quantumStatus.backends.isEmpty
                    ? 'Bekliyor'
                    : '${controller.quantumStatus.backends.first.qubits}q',
                controller.quantumStatus.connected ? .92 : .35,
              ),
            ],
          ),
          const SizedBox(height: 18),
          const FlowStrip(),
          const SizedBox(height: 18),
          PrimaryFooter(
            icon: Icons.play_arrow,
            label: 'Random audit hazırla',
            onPressed: () => controller.setScreen(2),
          ),
        ],
      ),
    );
  }
}

class AnalysisWorkspaceScreen extends StatelessWidget {
  const AnalysisWorkspaceScreen({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final health = controller.dataHealth;
    final qpu = controller.quantumStatus;
    return AppFrame(
      child: ListView(
        physics: const BouncingScrollPhysics(),
        padding: EdgeInsets.zero,
        children: [
          HeaderBlock(
            icon: Icons.analytics_outlined,
            title: 'Analiz merkezi',
            subtitle:
                '${controller.selectedGame.name} için veri, random ve QPU durumu.',
          ),
          const SizedBox(height: 16),
          MetricGrid(
            metrics: [
              MetricItem('Satır', '${health.rows}', .84),
              MetricItem(
                'Veri',
                health.ready ? 'Hazır' : 'Sınırlı',
                health.ready ? .95 : .35,
              ),
              MetricItem(
                'QPU',
                qpu.connected ? 'Bağlı' : 'Bekliyor',
                qpu.connected ? .92 : .35,
              ),
              MetricItem(
                'Backend',
                qpu.backends.isEmpty ? '-' : qpu.backends.first.name,
                .72,
              ),
            ],
          ),
          const SizedBox(height: 16),
          InfoBand(
            icon: health.ready
                ? Icons.check_circle_outline
                : Icons.warning_amber,
            text:
                health.issue ??
                'Veri kalite kontrolü geçti; random fingerprint için hazır.',
          ),
          const SizedBox(height: 18),
          const Text(
            'Random fingerprint',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 12),
          const ProgressMetric(label: 'Frekans sapması', value: .58),
          const ProgressMetric(label: 'Gap davranışı', value: .42),
          const ProgressMetric(label: 'Pair clustering', value: .64),
          const ProgressMetric(label: 'Takvim etkisi', value: .31),
          const SizedBox(height: 16),
          const Text(
            'IBM Quantum job',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 12),
          JobStep(
            done: true,
            label: 'Veri hazır',
            value: '${health.rows} satır',
          ),
          const JobStep(done: true, label: 'Model suite', value: '15 model'),
          JobStep(
            done: qpu.connected,
            label: 'IBM QPU',
            value: qpu.connected
                ? '${qpu.backends.length} backend'
                : 'Kontrol et',
          ),
          const JobStep(done: false, label: 'Gerçek run', value: 'Onay bekler'),
          const SizedBox(height: 12),
          PrimaryFooter(
            icon: Icons.sync,
            label: 'Analizi yenile',
            onPressed: () {
              controller.refreshDataHealth();
              controller.refreshQuantumStatus();
            },
          ),
        ],
      ),
    );
  }
}

class CouponWorkspaceScreen extends StatelessWidget {
  const CouponWorkspaceScreen({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    return AppFrame(
      child: ListView(
        physics: const BouncingScrollPhysics(),
        padding: EdgeInsets.zero,
        children: [
          HeaderBlock(
            icon: Icons.confirmation_number_outlined,
            title: 'Kupon oluştur',
            subtitle:
                '${controller.portfolio.columns} kolon, ${controller.selectedGame.drawKind}.',
          ),
          const SizedBox(height: 16),
          MetricGrid(
            metrics: [
              MetricItem(
                'Union',
                '${controller.portfolio.unionCoverage}/60',
                1,
              ),
              MetricItem('2+', percent(controller.portfolio.anyTwoPlus), .98),
              MetricItem('3+', percent(controller.portfolio.anyThreePlus), .53),
              const MetricItem('Garanti', 'Yok', .1),
            ],
          ),
          const SizedBox(height: 18),
          const ProgressMetric(label: 'Kolon kapasitesi', value: .30),
          const ProgressMetric(label: 'Overlap freni', value: .72),
          const ProgressMetric(label: 'Coverage hedefi', value: 1),
          const ProgressMetric(label: 'Pair/triple çeşitliliği', value: .68),
          const SizedBox(height: 18),
          const Text(
            'Örnek portföy',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 12),
          for (
            var index = 0;
            index < controller.portfolio.tickets.length;
            index++
          ) ...[
            CouponTile(
              index: index + 1,
              ticket: controller.portfolio.tickets[index],
            ),
            const SizedBox(height: 10),
          ],
          PrimaryFooter(
            icon: Icons.auto_fix_high,
            label: 'Yeni portföy üret',
            onPressed: () {},
          ),
        ],
      ),
    );
  }
}

class SettingsWorkspaceScreen extends StatefulWidget {
  const SettingsWorkspaceScreen({super.key, required this.controller});

  final AppController controller;

  @override
  State<SettingsWorkspaceScreen> createState() =>
      _SettingsWorkspaceScreenState();
}

class _SettingsWorkspaceScreenState extends State<SettingsWorkspaceScreen> {
  late final TextEditingController _tokenController;

  @override
  void initState() {
    super.initState();
    _tokenController = TextEditingController();
  }

  @override
  void dispose() {
    _tokenController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    return AppFrame(
      child: ListView(
        physics: const BouncingScrollPhysics(),
        padding: EdgeInsets.zero,
        children: [
          const HeaderBlock(
            icon: Icons.settings_outlined,
            title: 'Ayarlar',
            subtitle: 'IBM token ve Quantum Gateway bağlantısı.',
          ),
          const SizedBox(height: 18),
          TextField(
            controller: _tokenController,
            obscureText: true,
            onChanged: controller.setIbmTokenInput,
            decoration: InputDecoration(
              labelText: 'IBM Quantum token',
              suffixIcon: IconButton(
                tooltip: 'Temizle',
                onPressed: () {
                  _tokenController.clear();
                  controller.setIbmTokenInput('');
                },
                icon: const Icon(Icons.close),
              ),
              helperText: 'Repo’ya yazılmaz; local Qiskit hesabına kaydedilir.',
            ),
          ),
          const SizedBox(height: 14),
          InfoBand(
            icon: Icons.key,
            text: controller.gatewayOnline
                ? 'Gateway Qiskit hesabını kontrol edebilir; token repo dışındadır.'
                : 'Gateway kapalıysa app demo modunda çalışır.',
          ),
          const SizedBox(height: 16),
          SettingRow(
            label: 'Mod',
            value: controller.gatewayOnline ? 'Gateway' : 'Demo',
          ),
          SettingRow(
            label: 'IBM hesabı',
            value: controller.quantumStatus.connected ? 'Bağlı' : 'Bekliyor',
          ),
          const SettingRow(label: 'API güvenliği', value: 'Repo dışı'),
          const SizedBox(height: 12),
          PrimaryFooter(
            icon: Icons.key,
            label: controller.ibmTokenInput.isEmpty
                ? 'IBM bağlantısını kontrol et'
                : 'Tokeni lokal kaydet',
            onPressed: controller.ibmTokenInput.isEmpty
                ? controller.boot
                : () async {
                    await controller.saveIbmToken();
                    if (mounted && controller.ibmTokenInput.isEmpty) {
                      _tokenController.clear();
                    }
                  },
          ),
        ],
      ),
    );
  }
}

class LotteryScreen extends StatelessWidget {
  const LotteryScreen({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    return AppFrame(
      child: ListView.separated(
        itemCount: controller.games.length + 1,
        separatorBuilder: (context, index) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          if (index == 0) {
            return const HeaderBlock(
              icon: Icons.casino_outlined,
              title: 'Loto seç',
              subtitle: 'Model önce veriyi denetler, sonra audit üretir.',
            );
          }
          final game = controller.games[index - 1];
          return LotteryTile(
            game: game,
            selected: game.slug == controller.selectedGame.slug,
            onTap: () => controller.selectGame(game),
          );
        },
      ),
    );
  }
}

class _Destination {
  const _Destination(this.label, this.icon);

  final String label;
  final IconData icon;
}

String percent(double value) => '%${(value * 100).toStringAsFixed(1)}';
