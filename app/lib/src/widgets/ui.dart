import 'package:flutter/material.dart';
import 'dart:math' as math;

import '../models.dart';

class AppFrame extends StatelessWidget {
  const AppFrame({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 104),
      child: child,
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
              Text(title, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 4),
              Text(subtitle),
            ],
          ),
        ),
      ],
    );
  }
}

class IconFrame extends StatelessWidget {
  const IconFrame({super.key, required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        color: const Color(0xFFE2F2EF),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFB7DCD5)),
      ),
      child: Icon(icon, color: const Color(0xFF0F766E)),
    );
  }
}

class PremiumBackdrop extends StatelessWidget {
  const PremiumBackdrop({super.key, required this.progress});

  final double progress;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _QuantumBackdropPainter(progress),
      child: const SizedBox.expand(),
    );
  }
}

class QuantumHeroCard extends StatelessWidget {
  const QuantumHeroCard({super.key, required this.progress});

  final double progress;

  @override
  Widget build(BuildContext context) {
    final numbers = [7, 14, 37, 41, 43, 51];
    return Container(
      height: 222,
      decoration: BoxDecoration(
        color: const Color(0xFF0B2226),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF245A58)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x6610C8B0),
            blurRadius: 28,
            offset: Offset(0, 18),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Stack(
          children: [
            Positioned.fill(
              child: CustomPaint(painter: _OrbitPainter(progress)),
            ),
            Positioned(
              left: 18,
              top: 18,
              right: 18,
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'KuponIQ Quantum',
                      style: TextStyle(
                        color: Color(0xFFE9FFFA),
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  StatusPill(label: 'Quantum', tone: PillTone.good),
                ],
              ),
            ),
            Positioned(
              left: 18,
              right: 18,
              bottom: 18,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final number in numbers) NumberBall(number: number),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class PremiumTopBar extends StatelessWidget {
  const PremiumTopBar({
    super.key,
    required this.gatewayOnline,
    required this.onRefresh,
  });

  final bool gatewayOnline;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(
          child: Text(
            'KuponIQ',
            style: TextStyle(
              color: Color(0xFFE9FFFA),
              fontSize: 30,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        IconButton.filledTonal(
          tooltip: 'Yenile',
          onPressed: onRefresh,
          icon: const Icon(Icons.sync),
        ),
        const SizedBox(width: 8),
        StatusPill(
          label: gatewayOnline ? 'Gateway' : 'Demo',
          tone: gatewayOnline ? PillTone.good : PillTone.warn,
        ),
      ],
    );
  }
}

class FloatingNavBar extends StatelessWidget {
  const FloatingNavBar({
    super.key,
    required this.items,
    required this.selectedIndex,
    required this.onSelected,
  });

  final List<(String, IconData)> items;
  final int selectedIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
        decoration: const BoxDecoration(
          color: Color(0xF20A1D20),
          border: Border(top: BorderSide(color: Color(0xFF244246))),
        ),
        child: NavigationBar(
          height: 70,
          elevation: 0,
          backgroundColor: Colors.transparent,
          indicatorColor: const Color(0xFF18B7A0),
          selectedIndex: selectedIndex,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          onDestinationSelected: onSelected,
          destinations: [
            for (final item in items)
              NavigationDestination(
                icon: Icon(item.$2, color: const Color(0xFFBFE5DE)),
                selectedIcon: Icon(item.$2, color: const Color(0xFF031616)),
                label: item.$1,
              ),
          ],
        ),
      ),
    );
  }
}

class MetricItem {
  const MetricItem(this.label, this.value, this.progress);

  final String label;
  final String value;
  final double progress;
}

class MetricGrid extends StatelessWidget {
  const MetricGrid({super.key, required this.metrics});

  final List<MetricItem> metrics;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final columns = width > 620 ? 4 : 2;
        return GridView.count(
          crossAxisCount: columns,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: width > 620 ? 1.55 : 1.35,
          children: [for (final item in metrics) MetricCard(item: item)],
        );
      },
    );
  }
}

class MetricCard extends StatelessWidget {
  const MetricCard({super.key, required this.item});

  final MetricItem item;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item.label, style: Theme.of(context).textTheme.labelMedium),
            const Spacer(),
            Text(
              item.value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                minHeight: 6,
                value: item.progress.clamp(0, 1),
                backgroundColor: const Color(0xFF1B3B3F),
                color: const Color(0xFF18B7A0),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ProgressMetric extends StatelessWidget {
  const ProgressMetric({super.key, required this.label, required this.value});

  final String label;
  final double value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          SizedBox(width: 142, child: Text(label)),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                minHeight: 7,
                value: value.clamp(0, 1),
                backgroundColor: const Color(0xFF1B3B3F),
                color: const Color(0xFF18B7A0),
              ),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 46,
            child: Text(
              '%${(value * 100).round()}',
              textAlign: TextAlign.end,
              style: Theme.of(context).textTheme.labelLarge,
            ),
          ),
        ],
      ),
    );
  }
}

class LotteryTile extends StatelessWidget {
  const LotteryTile({
    super.key,
    required this.game,
    required this.selected,
    required this.onTap,
  });

  final LotteryGame game;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: selected ? const Color(0xFF123A3B) : const Color(0xFF10272B),
      child: ListTile(
        onTap: onTap,
        leading: IconFrame(icon: Icons.casino_outlined),
        title: Text(game.name),
        subtitle: Text('${game.drawKind} · ${game.displayStatus}'),
        trailing: selected
            ? const Icon(Icons.check_circle, color: Color(0xFF0F766E))
            : const Icon(Icons.chevron_right),
      ),
    );
  }
}

class FlowStrip extends StatelessWidget {
  const FlowStrip({super.key});

  @override
  Widget build(BuildContext context) {
    const steps = [
      ('Veri', Icons.dataset_outlined),
      ('Audit', Icons.analytics_outlined),
      ('QPU', Icons.memory),
      ('Kupon', Icons.confirmation_number_outlined),
    ];
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final step in steps)
          Chip(avatar: Icon(step.$2, size: 18), label: Text(step.$1)),
      ],
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
        color: const Color(0xFFFFF8E6),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE9D79E)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: const Color(0xFF8A6410)),
            const SizedBox(width: 10),
            Expanded(child: Text(text)),
          ],
        ),
      ),
    );
  }
}

enum PillTone { good, warn }

class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.label, required this.tone});

  final String label;
  final PillTone tone;

  @override
  Widget build(BuildContext context) {
    final good = tone == PillTone.good;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: good ? const Color(0xFFE4F7EA) : const Color(0xFFFFF1D5),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: good ? const Color(0xFF95D9A8) : const Color(0xFFE8C070),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text(label, style: const TextStyle(color: Color(0xFF102525))),
      ),
    );
  }
}

class SettingRow extends StatelessWidget {
  const SettingRow({super.key, required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        child: Row(
          children: [
            Expanded(child: Text(label)),
            Text(value, style: Theme.of(context).textTheme.titleMedium),
          ],
        ),
      ),
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
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Icon(
            done ? Icons.check_circle : Icons.radio_button_unchecked,
            color: done ? const Color(0xFF0F766E) : const Color(0xFF8A6410),
          ),
          const SizedBox(width: 10),
          Expanded(child: Text(label)),
          Text(value, style: Theme.of(context).textTheme.labelLarge),
        ],
      ),
    );
  }
}

class PrimaryFooter extends StatelessWidget {
  const PrimaryFooter({
    super.key,
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: onPressed,
        icon: Icon(icon),
        label: Text(label),
      ),
    );
  }
}

class CouponTile extends StatelessWidget {
  const CouponTile({super.key, required this.index, required this.ticket});

  final int index;
  final CouponTicket ticket;

  @override
  Widget build(BuildContext context) {
    return Card(
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
                  for (final number in ticket.main) NumberBall(number: number),
                ],
              ),
            ),
          ],
        ),
      ),
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
      decoration: BoxDecoration(
        color: const Color(0xFFE9FFFA),
        borderRadius: BorderRadius.circular(999),
        boxShadow: const [BoxShadow(color: Color(0x6618B7A0), blurRadius: 16)],
      ),
      child: Text(
        number.toString(),
        style: const TextStyle(
          color: Color(0xFF06191B),
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _QuantumBackdropPainter extends CustomPainter {
  _QuantumBackdropPainter(this.progress);

  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint();
    final rect = Offset.zero & size;
    paint.shader = const LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [Color(0xFF071A1D), Color(0xFF0F3033), Color(0xFF071A1D)],
    ).createShader(rect);
    canvas.drawRect(rect, paint);

    final linePaint = Paint()
      ..color = const Color(0x1F7EE8D7)
      ..strokeWidth = 1;
    for (var i = 0; i < 14; i++) {
      final y = (i * 58 + progress * 26) % size.height;
      canvas.drawLine(Offset(0, y), Offset(size.width, y + 42), linePaint);
    }

    final glowPaint = Paint()..color = const Color(0x3318B7A0);
    canvas.drawCircle(
      Offset(
        size.width * .82,
        size.height * (.12 + .03 * math.sin(progress * math.pi * 2)),
      ),
      118,
      glowPaint,
    );
    canvas.drawCircle(
      Offset(size.width * .08, size.height * .78),
      92,
      glowPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _QuantumBackdropPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}

class _OrbitPainter extends CustomPainter {
  _OrbitPainter(this.progress);

  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width * .5, size.height * .54);
    final ringPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.4
      ..color = const Color(0x557EE8D7);
    for (var i = 0; i < 4; i++) {
      final rect = Rect.fromCenter(
        center: center,
        width: 130 + i * 48,
        height: 56 + i * 34,
      );
      canvas.save();
      canvas.translate(center.dx, center.dy);
      canvas.rotate(progress * math.pi * 2 + i * .62);
      canvas.translate(-center.dx, -center.dy);
      canvas.drawOval(rect, ringPaint);
      canvas.restore();
    }

    for (var i = 0; i < 9; i++) {
      final angle = progress * math.pi * 2 + i * math.pi * 2 / 9;
      final radius = 34.0 + (i % 3) * 28;
      final dot = Offset(
        center.dx + math.cos(angle) * radius,
        center.dy + math.sin(angle) * radius,
      );
      canvas.drawCircle(dot, 3.8, Paint()..color = const Color(0xFFE9FFFA));
    }
  }

  @override
  bool shouldRepaint(covariant _OrbitPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}
