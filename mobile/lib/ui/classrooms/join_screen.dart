import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/classrooms/classrooms_providers.dart';
import '../../theme/app_colors.dart';
import 'classroom_detail_screen.dart';

/// Landing for an invite deep link (`prognos://join/{token}`). Previews the
/// class (public endpoint), then joins on confirm.
class JoinScreen extends ConsumerStatefulWidget {
  const JoinScreen({super.key, required this.token});
  final String token;

  @override
  ConsumerState<JoinScreen> createState() => _JoinScreenState();
}

class _JoinScreenState extends ConsumerState<JoinScreen> {
  bool _joining = false;

  Future<void> _join() async {
    setState(() => _joining = true);
    try {
      final classroom =
          await ref.read(classroomsApiProvider).join(widget.token);
      await ref.read(classroomsListProvider.notifier).refresh();
      if (!mounted) return;
      Navigator.of(context).pushReplacement(MaterialPageRoute(
          builder: (_) => ClassroomDetailScreen(classroomId: classroom.id)));
    } catch (_) {
      if (mounted) {
        setState(() => _joining = false);
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not join — invite may be invalid')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final preview = ref.watch(_joinPreviewProvider(widget.token));
    return Scaffold(
      appBar: AppBar(title: const Text('Join class')),
      body: preview.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _invalid(),
        data: (p) {
          if (!p.isValid) return _invalid();
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.groups_rounded,
                      size: 48, color: AppColors.primary400),
                  const SizedBox(height: 16),
                  Text(p.classroomName ?? 'Class',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.w700)),
                  const SizedBox(height: 6),
                  Text('${p.memberCount ?? 0} members',
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 13)),
                  const SizedBox(height: 24),
                  FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.primary500,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 40, vertical: 14),
                    ),
                    onPressed: _joining ? null : _join,
                    child: Text(_joining ? 'Joining…' : 'Join class',
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _invalid() => const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.link_off_rounded, size: 48, color: AppColors.danger400),
              SizedBox(height: 16),
              Text('This invite is invalid or has expired',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textSecondary, fontSize: 15)),
            ],
          ),
        ),
      );
}

final _joinPreviewProvider = FutureProvider.family((ref, String token) async {
  return ref.watch(classroomsApiProvider).joinPreview(token);
});
