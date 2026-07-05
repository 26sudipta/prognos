import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/analytics/analytics_providers.dart';
import '../../core/auth/auth_controller.dart';
import '../../core/contests/contests_providers.dart';
import '../../core/reminders/reminders_providers.dart';
import '../../core/widget/home_widget_service.dart';
import '../../theme/app_colors.dart';
import '../classrooms/classrooms_screen.dart';
import '../classrooms/join_screen.dart';
import '../contests/contests_screen.dart';
import '../contests/widgets/contest_detail_sheet.dart';
import '../dashboard/dashboard_screen.dart';
import '../reminders/reminders_screen.dart';

/// Root navigation shell — three primary tabs matching the v1 information
/// architecture (mobile plan §7). Also the home for reminder lifecycle wiring:
/// it initializes the scheduler, reconciles on foreground + cache updates, and
/// routes reminder taps to the contest detail sheet.
class HomeShell extends ConsumerStatefulWidget {
  const HomeShell({super.key});

  @override
  ConsumerState<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends ConsumerState<HomeShell>
    with WidgetsBindingObserver {
  int _index = 0;
  bool _remindersReady = false;
  String? _pendingDeepLink;
  StreamSubscription<String>? _tapSub;
  AppLinks? _appLinks;
  StreamSubscription<Uri>? _linkSub;

  static const _titles = ['Dashboard', 'Contests', 'Classes'];
  static const _bodies = <Widget>[
    DashboardScreen(),
    ContestsScreen(),
    ClassroomsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _bootstrapReminders();
      _bootstrapDeepLinks();
    });
  }

  @override
  void dispose() {
    _tapSub?.cancel();
    _linkSub?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  /// Wire `prognos://join/{token}` invite deep links (cold-launch + while running).
  Future<void> _bootstrapDeepLinks() async {
    _appLinks = AppLinks();
    try {
      final initial = await _appLinks!.getInitialLink();
      if (initial != null) _handleDeepLink(initial);
    } catch (_) {}
    _linkSub = _appLinks!.uriLinkStream.listen(_handleDeepLink);
  }

  void _handleDeepLink(Uri uri) {
    // prognos://join/{token}
    if (uri.host != 'join' || uri.pathSegments.isEmpty) return;
    final token = uri.pathSegments.first;
    if (token.isEmpty || !mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => JoinScreen(token: token)),
    );
  }

  /// One-time reminder init: start the scheduler, wire tap handling (running +
  /// cold-launch), then reconcile against the current cache.
  Future<void> _bootstrapReminders() async {
    final scheduler = ref.read(reminderSchedulerProvider);
    await scheduler.init();
    _remindersReady = true;

    _tapSub = scheduler.taps.listen(_openContest);
    _pendingDeepLink = await scheduler.initialLaunchContestId();

    await _reconcile();
    _tryOpenPendingDeepLink();
  }

  Future<void> _reconcile() async {
    if (!_remindersReady) return;
    await ref.read(remindersControllerProvider.notifier).refresh();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Foreground is the reconcile guarantee (esp. iOS): re-check reminders and
    // free/refill the pending set as contests pass.
    if (state == AppLifecycleState.resumed) _reconcile();
  }

  void _openContest(String contestId) {
    final contests = ref.read(contestsProvider).value?.contests ?? const [];
    for (final c in contests) {
      if (c.id == contestId) {
        if (mounted) ContestDetailSheet.show(context, c);
        return;
      }
    }
    // Cache not loaded yet — defer until it is.
    _pendingDeepLink = contestId;
  }

  void _tryOpenPendingDeepLink() {
    final id = _pendingDeepLink;
    if (id == null) return;
    final contests = ref.read(contestsProvider).value?.contests ?? const [];
    for (final c in contests) {
      if (c.id == id) {
        _pendingDeepLink = null;
        if (mounted) ContestDetailSheet.show(context, c);
        return;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authControllerProvider).value;

    // Reconcile whenever the contest cache updates (initial load, refresh, sync)
    // and flush any pending deep link once contests are available.
    ref.listen(contestsProvider, (prev, next) {
      if (next.hasValue) {
        _reconcile();
        _tryOpenPendingDeepLink();
        updateHomeWidget(ref.read(appDatabaseProvider));
      }
    });
    // Streak comes from analytics — refresh the widget when it changes too.
    ref.listen(analyticsProvider, (prev, next) {
      if (next.hasValue) updateHomeWidget(ref.read(appDatabaseProvider));
    });

    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_index], style: const TextStyle(fontWeight: FontWeight.w700)),
        actions: [
          if (user != null)
            Padding(
              padding: const EdgeInsets.only(right: 4),
              child: Center(
                child: Text(
                  user.name.split(' ').first,
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
                ),
              ),
            ),
          IconButton(
            tooltip: 'Reminders',
            icon: const Icon(Icons.notifications_none_rounded, size: 21),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const RemindersScreen()),
            ),
          ),
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout_rounded, size: 20),
            onPressed: () => ref.read(authControllerProvider.notifier).signOut(),
          ),
        ],
      ),
      body: IndexedStack(index: _index, children: _bodies),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.insights_outlined),
            selectedIcon: Icon(Icons.insights_rounded),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.event_outlined),
            selectedIcon: Icon(Icons.event_rounded),
            label: 'Contests',
          ),
          NavigationDestination(
            icon: Icon(Icons.groups_outlined),
            selectedIcon: Icon(Icons.groups_rounded),
            label: 'Classes',
          ),
        ],
      ),
    );
  }
}
