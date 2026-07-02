import 'package:flutter/material.dart';

import 'placeholder_screen.dart';

/// Root navigation shell — three primary tabs matching the v1 information
/// architecture (mobile plan §7). Uses an [IndexedStack] so tab state is
/// preserved when switching. Real screens replace the placeholders per slice.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  static const _tabs = <Widget>[
    PlaceholderScreen(title: 'Dashboard', icon: Icons.insights_rounded, milestone: 'M4'),
    PlaceholderScreen(title: 'Contests', icon: Icons.event_rounded, milestone: 'M2'),
    PlaceholderScreen(title: 'Leaderboard', icon: Icons.leaderboard_rounded, milestone: 'M5'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _tabs),
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
            icon: Icon(Icons.leaderboard_outlined),
            selectedIcon: Icon(Icons.leaderboard_rounded),
            label: 'Leaderboard',
          ),
        ],
      ),
    );
  }
}
