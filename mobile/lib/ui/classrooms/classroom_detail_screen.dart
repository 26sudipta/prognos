import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/classrooms/classroom_models.dart';
import '../../core/classrooms/classrooms_providers.dart';
import '../../theme/app_colors.dart';
import '../../theme/cf_rating.dart';

/// Classroom detail: leaderboard (cached-first) + members, plus cohort +
/// invites for teachers. Sync triggers a bulk refresh; the app-bar menu
/// leaves (student) or deletes (teacher).
class ClassroomDetailScreen extends ConsumerWidget {
  const ClassroomDetailScreen({super.key, required this.classroomId});
  final String classroomId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final classroomAsync = ref.watch(classroomProvider(classroomId));

    return classroomAsync.when(
      loading: () => const Scaffold(
          body: Center(child: CircularProgressIndicator())),
      error: (e, _) => Scaffold(
        appBar: AppBar(),
        body: Center(child: Text('Could not load class\n$e')),
      ),
      data: (classroom) {
        final teacher = classroom.isTeacher;
        final tabs = <Tab>[
          const Tab(text: 'Leaderboard'),
          const Tab(text: 'Members'),
          if (teacher) const Tab(text: 'Cohort'),
          if (teacher) const Tab(text: 'Invites'),
        ];
        return DefaultTabController(
          length: tabs.length,
          child: Scaffold(
            appBar: AppBar(
              title: Text(classroom.name),
              actions: [
                IconButton(
                  tooltip: 'Sync',
                  icon: const Icon(Icons.sync_rounded),
                  onPressed: () => syncClassroom(ref, classroomId),
                ),
                _OverflowMenu(classroom: classroom),
              ],
              bottom: TabBar(
                isScrollable: true,
                tabAlignment: TabAlignment.start,
                labelColor: AppColors.primary400,
                unselectedLabelColor: AppColors.textMuted,
                indicatorColor: AppColors.primary400,
                tabs: tabs,
              ),
            ),
            body: TabBarView(
              children: [
                _LeaderboardTab(classroomId: classroomId),
                _MembersTab(classroomId: classroomId, canManage: teacher),
                if (teacher) _CohortTab(classroomId: classroomId),
                if (teacher) _InvitesTab(classroomId: classroomId),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _OverflowMenu extends ConsumerWidget {
  const _OverflowMenu({required this.classroom});
  final Classroom classroom;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return PopupMenuButton<String>(
      onSelected: (v) => _handle(context, ref, v),
      itemBuilder: (_) => [
        if (classroom.isTeacher)
          const PopupMenuItem(value: 'delete', child: Text('Delete class'))
        else
          const PopupMenuItem(value: 'leave', child: Text('Leave class')),
      ],
    );
  }

  Future<void> _handle(BuildContext context, WidgetRef ref, String v) async {
    final api = ref.read(classroomsApiProvider);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgSurface,
        title: Text(v == 'delete' ? 'Delete this class?' : 'Leave this class?',
            style: const TextStyle(color: AppColors.textPrimary)),
        content: Text(
          v == 'delete'
              ? 'This removes the class and its leaderboard for everyone.'
              : 'You can re-join later with an invite.',
          style: const TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger500),
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(v == 'delete' ? 'Delete' : 'Leave'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      if (v == 'delete') {
        await api.delete(classroom.id);
      } else {
        await api.leave(classroom.id);
      }
      await ref.read(classroomsListProvider.notifier).refresh();
      if (context.mounted) Navigator.of(context).pop();
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Action failed')));
      }
    }
  }
}

// ─── Leaderboard ────────────────────────────────────────────────────────────

class _LeaderboardTab extends ConsumerStatefulWidget {
  const _LeaderboardTab({required this.classroomId});
  final String classroomId;

  @override
  ConsumerState<_LeaderboardTab> createState() => _LeaderboardTabState();
}

class _LeaderboardTabState extends ConsumerState<_LeaderboardTab> {
  Timer? _poll;

  @override
  void dispose() {
    _poll?.cancel();
    super.dispose();
  }

  /// Poll every 5s while the board reports a bulk sync in progress.
  void _syncPolling(bool syncing) {
    if (syncing && _poll == null) {
      _poll = Timer.periodic(const Duration(seconds: 5),
          (_) => ref.invalidate(leaderboardProvider(widget.classroomId)));
    } else if (!syncing) {
      _poll?.cancel();
      _poll = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final classroomId = widget.classroomId;
    final async = ref.watch(leaderboardProvider(classroomId));
    _syncPolling(async.value?.syncing ?? false);
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (lb) => RefreshIndicator(
        color: AppColors.primary400,
        onRefresh: () async {
          ref.invalidate(leaderboardProvider(classroomId));
          await ref.read(leaderboardProvider(classroomId).future);
        },
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
          children: [
            if (lb.syncing)
              const Padding(
                padding: EdgeInsets.all(8),
                child: Row(children: [
                  SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: AppColors.primary400)),
                  SizedBox(width: 10),
                  Text('Syncing members…',
                      style: TextStyle(
                          color: AppColors.primary400, fontSize: 12.5)),
                ]),
              ),
            if (lb.entries.isEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 60),
                child: Center(
                    child: Text('No ranked members yet',
                        style: TextStyle(
                            color: AppColors.textMuted, fontSize: 14))),
              )
            else
              for (final e in lb.entries) _LeaderboardRow(entry: e),
          ],
        ),
      ),
    );
  }
}

class _LeaderboardRow extends StatelessWidget {
  const _LeaderboardRow({required this.entry});
  final LeaderboardEntry entry;

  @override
  Widget build(BuildContext context) {
    final ratingColor = CfRating.color(entry.cfRating);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        color: entry.isMe
            ? AppColors.primary500.withValues(alpha: 0.10)
            : AppColors.bgSurface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
            color: entry.isMe ? AppColors.primary500 : AppColors.borderSubtle),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 26,
            child: Text('${entry.rank}',
                textAlign: TextAlign.center,
                style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 14,
                    fontWeight: FontWeight.w700)),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(entry.cfHandle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                        color: ratingColor,
                        fontSize: 14,
                        fontWeight: FontWeight.w700)),
                Text(entry.userName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 11.5)),
              ],
            ),
          ),
          _Stat(label: 'Rating', value: entry.cfRating?.toString() ?? '—', color: ratingColor),
          _Stat(label: 'Solved', value: '${entry.solvedCount}'),
          _Stat(label: 'Streak', value: '${entry.currentStreak}'),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value, this.color});
  final String label;
  final String value;
  final Color? color;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(left: 12),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(
                    color: color ?? AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w700)),
            Text(label,
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 10)),
          ],
        ),
      );
}

// ─── Members ────────────────────────────────────────────────────────────────

class _MembersTab extends ConsumerWidget {
  const _MembersTab({required this.classroomId, required this.canManage});
  final String classroomId;
  final bool canManage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(membersProvider(classroomId));
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (members) => ListView(
        padding: const EdgeInsets.all(12),
        children: [
          for (final m in members)
            ListTile(
              title: Text(m.userName,
                  style: const TextStyle(color: AppColors.textPrimary)),
              subtitle: Text(m.cfHandle ?? m.role,
                  style: const TextStyle(color: AppColors.textMuted)),
              trailing: (canManage && m.role != 'teacher')
                  ? IconButton(
                      tooltip: 'Remove member',
                      icon: const Icon(Icons.person_remove_rounded,
                          size: 20, color: AppColors.danger400),
                      onPressed: () async {
                        await ref
                            .read(classroomsApiProvider)
                            .removeMember(classroomId, m.userId);
                        ref.invalidate(membersProvider(classroomId));
                      },
                    )
                  : null,
            ),
        ],
      ),
    );
  }
}

// ─── Cohort (teacher) ───────────────────────────────────────────────────────

class _CohortTab extends ConsumerWidget {
  const _CohortTab({required this.classroomId});
  final String classroomId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(cohortProvider(classroomId));
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (c) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _card('Class average rating',
              c.classAverageRating == null
                  ? '—'
                  : c.classAverageRating!.round().toString()),
          const SizedBox(height: 12),
          _tagCard('Most neglected tags', c.mostNeglectedTags),
          const SizedBox(height: 12),
          _tagCard('Lowest success tags', c.lowestSuccessTags),
          const SizedBox(height: 12),
          _attendanceCard(c.attendance),
        ],
      ),
    );
  }

  Widget _card(String title, String value) => Container(
        padding: const EdgeInsets.all(16),
        decoration: _dec,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title,
                style: const TextStyle(
                    color: AppColors.textSecondary, fontSize: 14)),
            Text(value,
                style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 20,
                    fontWeight: FontWeight.w800)),
          ],
        ),
      );

  Widget _tagCard(String title, List<CohortTag> tags) => Container(
        padding: const EdgeInsets.all(16),
        decoration: _dec,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            if (tags.isEmpty)
              const Text('—', style: TextStyle(color: AppColors.textMuted))
            else
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final t in tags)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: AppColors.bgSurfaceRaised,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text('${t.tag} · ${t.count}',
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 12.5)),
                    ),
                ],
              ),
          ],
        ),
      );

  Widget _attendanceCard(List<CohortAttendance> att) => Container(
        padding: const EdgeInsets.all(16),
        decoration: _dec,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Attendance (30d active days)',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            for (final a in att)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(a.userName,
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 13)),
                    Text('${a.daysActive30d}/30',
                        style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 13,
                            fontWeight: FontWeight.w600)),
                  ],
                ),
              ),
          ],
        ),
      );
}

const _dec = BoxDecoration(
  color: AppColors.bgSurface,
  borderRadius: BorderRadius.all(Radius.circular(14)),
  border: Border.fromBorderSide(BorderSide(color: AppColors.borderSubtle)),
);

// ─── Invites (teacher) ──────────────────────────────────────────────────────

class _InvitesTab extends ConsumerWidget {
  const _InvitesTab({required this.classroomId});
  final String classroomId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(invitesProvider(classroomId));
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (invites) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          FilledButton.icon(
            style: FilledButton.styleFrom(
                backgroundColor: AppColors.primary500,
                minimumSize: const Size(double.infinity, 48)),
            onPressed: () async {
              await ref.read(classroomsApiProvider).createInvite(classroomId);
              ref.invalidate(invitesProvider(classroomId));
            },
            icon: const Icon(Icons.add_link_rounded, size: 18),
            label: const Text('Generate invite link'),
          ),
          const SizedBox(height: 16),
          for (final inv in invites.where((i) => i.isActive))
            _InviteRow(classroomId: classroomId, invite: inv),
        ],
      ),
    );
  }
}

class _InviteRow extends ConsumerWidget {
  const _InviteRow({required this.classroomId, required this.invite});
  final String classroomId;
  final Invite invite;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: _dec,
      child: Row(
        children: [
          Expanded(
            child: Text(invite.inviteUrl,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                    color: AppColors.textSecondary, fontSize: 12.5)),
          ),
          IconButton(
            tooltip: 'Copy invite link',
            icon: const Icon(Icons.copy_rounded, size: 18),
            color: AppColors.textMuted,
            onPressed: () {
              Clipboard.setData(ClipboardData(text: invite.inviteUrl));
              ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Invite link copied')));
            },
          ),
          IconButton(
            tooltip: 'Revoke invite',
            icon: const Icon(Icons.delete_outline_rounded, size: 18),
            color: AppColors.danger400,
            onPressed: () async {
              await ref
                  .read(classroomsApiProvider)
                  .revokeInvite(classroomId, invite.id);
              ref.invalidate(invitesProvider(classroomId));
            },
          ),
        ],
      ),
    );
  }
}
