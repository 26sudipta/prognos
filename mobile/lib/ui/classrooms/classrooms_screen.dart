import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/classrooms/classroom_models.dart';
import '../../core/classrooms/classrooms_providers.dart';
import '../../theme/app_colors.dart';
import '../widgets/skeleton.dart';
import 'classroom_detail_screen.dart';

/// The "Classes" tab — the classrooms the user belongs to, cached-first, with
/// Create and Join actions.
class ClassroomsScreen extends ConsumerWidget {
  const ClassroomsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(classroomsListProvider);

    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primary500,
        onPressed: () => _showCreate(context, ref),
        icon: const Icon(Icons.add_rounded),
        label: const Text('New class'),
      ),
      body: async.when(
        loading: () => const _ListSkeleton(),
        error: (e, _) => Center(child: Text('$e')),
        data: (state) => RefreshIndicator(
          color: AppColors.primary400,
          backgroundColor: AppColors.bgSurfaceRaised,
          onRefresh: () => ref.read(classroomsListProvider.notifier).refresh(),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text('Classes',
                        style: TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 22,
                            fontWeight: FontWeight.w800)),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _showJoin(context, ref),
                    icon: const Icon(Icons.group_add_rounded, size: 18),
                    label: const Text('Join'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (state.classrooms.isEmpty)
                const _EmptyState()
              else
                for (final c in state.classrooms)
                  _ClassroomCard(classroom: c),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showCreate(BuildContext context, WidgetRef ref) async {
    final name = await _promptText(
      context,
      title: 'Create a class',
      hint: 'Class name',
      action: 'Create',
    );
    if (name == null || name.trim().isEmpty) return;
    try {
      final created =
          await ref.read(classroomsApiProvider).create(name.trim());
      await ref.read(classroomsListProvider.notifier).refresh();
      if (context.mounted) _open(context, created.id);
    } catch (_) {
      if (context.mounted) _toast(context, 'Could not create class');
    }
  }

  Future<void> _showJoin(BuildContext context, WidgetRef ref) async {
    final code = await _promptText(
      context,
      title: 'Join a class',
      hint: 'Invite code',
      action: 'Join',
    );
    if (code == null || code.trim().isEmpty) return;
    try {
      final joined = await ref.read(classroomsApiProvider).join(code.trim());
      await ref.read(classroomsListProvider.notifier).refresh();
      if (context.mounted) _open(context, joined.id);
    } catch (_) {
      if (context.mounted) _toast(context, 'Invalid or expired invite');
    }
  }

  void _open(BuildContext context, String id) => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ClassroomDetailScreen(classroomId: id)),
      );
}

void _toast(BuildContext context, String msg) =>
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

Future<String?> _promptText(
  BuildContext context, {
  required String title,
  required String hint,
  required String action,
}) {
  final controller = TextEditingController();
  return showDialog<String>(
    context: context,
    builder: (ctx) => AlertDialog(
      backgroundColor: AppColors.bgSurface,
      title: Text(title, style: const TextStyle(color: AppColors.textPrimary)),
      content: TextField(
        controller: controller,
        autofocus: true,
        style: const TextStyle(color: AppColors.textPrimary),
        decoration: InputDecoration(hintText: hint),
        onSubmitted: (v) => Navigator.of(ctx).pop(v),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel')),
        FilledButton(
          onPressed: () => Navigator.of(ctx).pop(controller.text),
          child: Text(action),
        ),
      ],
    ),
  );
}

class _ClassroomCard extends StatelessWidget {
  const _ClassroomCard({required this.classroom});
  final Classroom classroom;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: AppColors.bgSurface,
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) =>
                  ClassroomDetailScreen(classroomId: classroom.id))),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.borderSubtle),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(classroom.name,
                          style: const TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 16,
                              fontWeight: FontWeight.w700)),
                      const SizedBox(height: 4),
                      Text('${classroom.memberCount} members',
                          style: const TextStyle(
                              color: AppColors.textMuted, fontSize: 12.5)),
                    ],
                  ),
                ),
                if (classroom.isTeacher)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.accent500.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text('Teacher',
                        style: TextStyle(
                            color: AppColors.accent400,
                            fontSize: 11,
                            fontWeight: FontWeight.w700)),
                  ),
                const SizedBox(width: 6),
                const Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.only(top: 100),
        child: Column(
          children: [
            Icon(Icons.groups_rounded, size: 48, color: AppColors.textDisabled),
            SizedBox(height: 16),
            Text('No classes yet',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 15)),
            SizedBox(height: 6),
            Text('Create one, or join with an invite code.',
                style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ],
        ),
      );
}

class _ListSkeleton extends StatelessWidget {
  const _ListSkeleton();
  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          Skeleton(width: 120, height: 28),
          SizedBox(height: 16),
          Skeleton(height: 76, radius: 14),
          SizedBox(height: 10),
          Skeleton(height: 76, radius: 14),
        ],
      );
}
