import 'package:flutter/material.dart';

void main() => runApp(const KuponIqApp());

class KuponIqApp extends StatelessWidget {
  const KuponIqApp({super.key});

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF0F766E);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'KuponIQ Quantum',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF4F7F8),
        useMaterial3: true,
      ),
      home: const AppShell(),
    );
  }
}

class LotteryProduct {
  const LotteryProduct({
    required this.name,
    required this.rule,
    required this.status,
    required this.rows,
    required this.icon,
  });

  final String name;
  final String rule;
  final String status;
  final int rows;
  final IconData icon;
}

class Coupon {
  const Coupon(this.numbers);

  final List<int> numbers;
}

const products = [
  LotteryProduct(
    name: 'Çılgın Sayısal',
    rule: '6/90 + Joker',
    status: 'Veri hazır',
    rows: 1236,
    icon: Icons.blur_circular,
  ),
  LotteryProduct(
    name: 'Süper Loto',
    rule: '6/60',
    status: 'Veri hazır',
    rows: 1135,
    icon: Icons.grid_3x3,
  ),
  LotteryProduct(
    name: 'Şans Topu',
    rule: '5/34 + 1/14',
    status: 'Veri hazır',
    rows: 816,
    icon: Icons.add_circle_outline,
  ),
  LotteryProduct(
    name: 'On Numara',
    rule: '22/80 -> 10 kolon',
    status: 'Tarih kaynağı bekliyor',
    rows: 779,
    icon: Icons.filter_9_plus,
  ),
  LotteryProduct(
    name: 'Hızlı On',
    rule: '1-10/80',
    status: 'Adapter hazır',
    rows: 0,
    icon: Icons.speed,
  ),
];

const demoCoupons = [
  Coupon([7, 14, 37, 41, 43, 51]),
  Coupon([11, 15, 17, 18, 34, 60]),
  Coupon([2, 3, 16, 36, 48, 56]),
  Coupon([6, 8, 20, 32, 47, 52]),
  Coupon([21, 27, 29, 31, 42, 45]),
];

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      const WelcomeScreen(),
      const LoginScreen(),
      const LotteryPickerScreen(),
      const DataSyncScreen(),
      const RandomAuditScreen(),
      const QuantumJobScreen(),
      const CouponBuilderScreen(),
      const PortfolioScreen(),
      const BacktestScreen(),
      const SettingsScreen(),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('KuponIQ Quantum'),
        actions: [
          IconButton(
            tooltip: 'Bildirimler',
            onPressed: () {},
            icon: const Icon(Icons.notifications_none),
          ),
        ],
      ),
      body: pages[_index],
      bottomNavigationBar: ScreenPicker(
        selectedIndex: _index,
        onSelected: (value) => setState(() => _index = value),
      ),
    );
  }
}

class ScreenPicker extends StatelessWidget {
  const ScreenPicker({
    super.key,
    required this.selectedIndex,
    required this.onSelected,
  });

  final int selectedIndex;
  final ValueChanged<int> onSelected;

  static const labels = [
    ('Açılış', Icons.auto_awesome),
    ('Giriş', Icons.login),
    ('Lotolar', Icons.casino),
    ('Veri', Icons.dataset),
    ('Analiz', Icons.analytics),
    ('IBM', Icons.memory),
    ('Kur', Icons.tune),
    ('Kupon', Icons.confirmation_number),
    ('Test', Icons.bar_chart),
    ('Profil', Icons.person),
  ];

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SizedBox(
        height: 76,
        child: ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          scrollDirection: Axis.horizontal,
          itemCount: labels.length,
          separatorBuilder: (context, index) => const SizedBox(width: 8),
          itemBuilder: (context, index) {
            final item = labels[index];
            return ChoiceChip(
              selected: selectedIndex == index,
              avatar: Icon(item.$2, size: 18),
              label: Text(item.$1),
              onSelected: (_) => onSelected(index),
            );
          },
        ),
      ),
    );
  }
}

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const OrbitMark(),
          const SizedBox(height: 28),
          Text(
            'Rastgeleliği ölç. Kuponu hazırla.',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.w800,
              color: const Color(0xFF102A2A),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Türkiye loto arşivleri, IBM Quantum sampling ve portföy metrikleri tek akışta.',
          ),
          const Spacer(),
          FilledButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.arrow_forward),
            label: const Text('Başla'),
          ),
        ],
      ),
    );
  }
}

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        children: const [
          HeaderBlock(
            icon: Icons.lock_outline,
            title: 'Üyelik',
            subtitle: 'IBM token kullanıcının cihazında kalır.',
          ),
          SizedBox(height: 16),
          TextField(decoration: InputDecoration(labelText: 'E-posta')),
          SizedBox(height: 12),
          TextField(
            obscureText: true,
            decoration: InputDecoration(labelText: 'IBM Quantum token'),
          ),
          SizedBox(height: 18),
          ActionRow(label: 'IBM hesabını bağla', icon: Icons.key),
        ],
      ),
    );
  }
}

class LotteryPickerScreen extends StatelessWidget {
  const LotteryPickerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: ListView.separated(
        itemCount: products.length + 1,
        separatorBuilder: (context, index) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          if (index == 0) {
            return const HeaderBlock(
              icon: Icons.casino_outlined,
              title: 'Loto seç',
              subtitle: 'Model önce veriyi kontrol eder, sonra audit hazırlar.',
            );
          }
          final product = products[index - 1];
          return ProductTile(product: product);
        },
      ),
    );
  }
}

class DataSyncScreen extends StatelessWidget {
  const DataSyncScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const HeaderBlock(
            icon: Icons.dataset_outlined,
            title: 'Veri durumu',
            subtitle: 'Son 10 yıl arşivleri kalite kontrolünden geçer.',
          ),
          const SizedBox(height: 18),
          for (final product in products.take(4)) ...[
            MetricRow(
              label: product.name,
              value: product.rows == 0 ? 'Adapter' : '${product.rows} satır',
              progress: product.rows == 0 ? .35 : .92,
            ),
            const SizedBox(height: 12),
          ],
          const InfoBand(
            icon: Icons.warning_amber,
            text: 'Hızlı On yeni ürün; 10 yıllık kamu arşivi yok.',
          ),
        ],
      ),
    );
  }
}

class RandomAuditScreen extends StatelessWidget {
  const RandomAuditScreen({super.key});

  @override
  Widget build(BuildContext context) {
    const scores = [
      ('Frekans', .58),
      ('Gap', .42),
      ('Pair', .64),
      ('Triple', .74),
      ('Takvim', .67),
      ('Runs', .60),
    ];
    return ScreenFrame(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const HeaderBlock(
            icon: Icons.analytics_outlined,
            title: 'Random audit',
            subtitle: 'Fingerprint: zayıf sapma + yakın uniform.',
          ),
          const SizedBox(height: 14),
          for (final item in scores) ...[
            MetricRow(
              label: item.$1,
              value: '${(item.$2 * 100).round()}%',
              progress: item.$2,
            ),
            const SizedBox(height: 10),
          ],
          const InfoBand(
            icon: Icons.science_outlined,
            text: 'Audit öneri üretmez; sadece dağılımı sınıflandırır.',
          ),
        ],
      ),
    );
  }
}

class QuantumJobScreen extends StatelessWidget {
  const QuantumJobScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          HeaderBlock(
            icon: Icons.memory,
            title: 'IBM Quantum',
            subtitle: 'Random audit ve generation ayrı job olarak izlenir.',
          ),
          SizedBox(height: 20),
          JobStep(
            done: true,
            label: 'Random structure',
            value: '156q / 112 layer',
          ),
          JobStep(done: true, label: 'Counts sampling', value: '262.144 shot'),
          JobStep(done: false, label: 'Kupon post-process', value: 'Bekliyor'),
          Spacer(),
          InfoBand(
            icon: Icons.verified_user_outlined,
            text: 'Simulator fallback kapalı tutulabilir.',
          ),
        ],
      ),
    );
  }
}

class CouponBuilderScreen extends StatelessWidget {
  const CouponBuilderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const HeaderBlock(
            icon: Icons.tune,
            title: 'Kupon kur',
            subtitle: 'Kolon sayısı, kapsama ve overlap kontrol edilir.',
          ),
          const SizedBox(height: 18),
          const Text('Kolon sayısı'),
          Slider(value: 30, min: 1, max: 100, divisions: 99, onChanged: (_) {}),
          const Text('Risk dağılımı'),
          Slider(value: .62, onChanged: (_) {}),
          const Text('Kapsama hedefi'),
          Slider(value: 1, onChanged: (_) {}),
          const Spacer(),
          FilledButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.auto_fix_high),
            label: const Text('Kuponları hazırla'),
          ),
        ],
      ),
    );
  }
}

class PortfolioScreen extends StatelessWidget {
  const PortfolioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        children: [
          const HeaderBlock(
            icon: Icons.confirmation_number_outlined,
            title: 'Kupon portföyü',
            subtitle: '60/60 kapsama, max overlap 3.',
          ),
          const SizedBox(height: 14),
          Expanded(
            child: ListView.separated(
              itemCount: demoCoupons.length,
              separatorBuilder: (context, index) => const SizedBox(height: 10),
              itemBuilder: (context, index) =>
                  CouponTile(index: index + 1, coupon: demoCoupons[index]),
            ),
          ),
          const ActionRow(label: 'Paylaş / dışa aktar', icon: Icons.ios_share),
        ],
      ),
    );
  }
}

class BacktestScreen extends StatelessWidget {
  const BacktestScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          HeaderBlock(
            icon: Icons.bar_chart,
            title: 'Backtest',
            subtitle: 'Portföy geçmişe karşı ölçülür.',
          ),
          SizedBox(height: 18),
          MetricRow(label: 'En az 2+', value: '%97.69', progress: .9769),
          SizedBox(height: 12),
          MetricRow(label: 'En az 3+', value: '%52.69', progress: .5269),
          SizedBox(height: 12),
          MetricRow(label: 'Rastgele 3+ baz', value: '%26.80', progress: .268),
          Spacer(),
          InfoBand(
            icon: Icons.info_outline,
            text: 'Garanti değil; risk optimizasyonu ve araştırma çıktısı.',
          ),
        ],
      ),
    );
  }
}

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenFrame(
      child: Column(
        children: const [
          HeaderBlock(
            icon: Icons.person_outline,
            title: 'Profil',
            subtitle: 'Üyelik, token ve sorumlu oyun limitleri.',
          ),
          SizedBox(height: 16),
          SettingsTile(
            icon: Icons.workspace_premium,
            label: 'Paket',
            value: 'Pro deneme',
          ),
          SettingsTile(icon: Icons.key, label: 'IBM token', value: 'Cihazda'),
          SettingsTile(
            icon: Icons.timer,
            label: 'Oyun limiti',
            value: 'Günlük 30 dk',
          ),
          SettingsTile(
            icon: Icons.storage,
            label: 'Veri cache',
            value: '4 dosya hazır',
          ),
          SettingsTile(icon: Icons.code, label: 'GitHub', value: 'Public repo'),
        ],
      ),
    );
  }
}

class ScreenFrame extends StatelessWidget {
  const ScreenFrame({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(padding: const EdgeInsets.all(18), child: child),
    );
  }
}

class HeaderBlock extends StatelessWidget {
  const HeaderBlock({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        IconFrame(icon: icon),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              Text(subtitle),
            ],
          ),
        ),
      ],
    );
  }
}

class ProductTile extends StatelessWidget {
  const ProductTile({super.key, required this.product});

  final LotteryProduct product;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE0E7E7)),
      ),
      child: ListTile(
        leading: IconFrame(icon: product.icon),
        title: Text(product.name),
        subtitle: Text('${product.rule} · ${product.status}'),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}

class CouponTile extends StatelessWidget {
  const CouponTile({super.key, required this.index, required this.coupon});

  final int index;
  final Coupon coupon;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE0E7E7)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Text(index.toString().padLeft(2, '0')),
            const SizedBox(width: 12),
            Expanded(
              child: Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  for (final number in coupon.numbers)
                    NumberBall(number: number),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class MetricRow extends StatelessWidget {
  const MetricRow({
    super.key,
    required this.label,
    required this.value,
    required this.progress,
  });

  final String label;
  final String value;
  final double progress;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: Text(label)),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
          ],
        ),
        const SizedBox(height: 6),
        LinearProgressIndicator(value: progress.clamp(0, 1)),
      ],
    );
  }
}

class JobStep extends StatelessWidget {
  const JobStep({
    super.key,
    required this.done,
    required this.label,
    required this.value,
  });

  final bool done;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          Icon(done ? Icons.check_circle : Icons.radio_button_unchecked),
          const SizedBox(width: 12),
          Expanded(child: Text(label)),
          Text(value),
        ],
      ),
    );
  }
}

class SettingsTile extends StatelessWidget {
  const SettingsTile({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: IconFrame(icon: icon),
      title: Text(label),
      trailing: Text(value),
    );
  }
}

class ActionRow extends StatelessWidget {
  const ActionRow({super.key, required this.label, required this.icon});

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: () {},
        icon: Icon(icon),
        label: Text(label),
      ),
    );
  }
}

class InfoBand extends StatelessWidget {
  const InfoBand({super.key, required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7E6),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFFB45309)),
            const SizedBox(width: 10),
            Expanded(child: Text(text)),
          ],
        ),
      ),
    );
  }
}

class IconFrame extends StatelessWidget {
  const IconFrame({super.key, required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 42,
      height: 42,
      decoration: BoxDecoration(
        color: const Color(0xFFE6F4F1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: const Color(0xFF0F766E)),
    );
  }
}

class NumberBall extends StatelessWidget {
  const NumberBall({super.key, required this.number});

  final int number;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 34,
      height: 34,
      alignment: Alignment.center,
      decoration: const BoxDecoration(
        color: Color(0xFF102A2A),
        shape: BoxShape.circle,
      ),
      child: Text(
        number.toString().padLeft(2, '0'),
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w800,
          fontSize: 12,
        ),
      ),
    );
  }
}

class OrbitMark extends StatelessWidget {
  const OrbitMark({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 210,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: 170,
            height: 170,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFF99F6E4), width: 2),
            ),
          ),
          const Icon(Icons.memory, size: 70, color: Color(0xFF0F766E)),
          const Positioned(top: 20, left: 58, child: NumberBall(number: 7)),
          const Positioned(right: 50, top: 68, child: NumberBall(number: 23)),
          const Positioned(left: 62, bottom: 30, child: NumberBall(number: 48)),
          const Positioned(
            right: 82,
            bottom: 18,
            child: NumberBall(number: 60),
          ),
        ],
      ),
    );
  }
}
