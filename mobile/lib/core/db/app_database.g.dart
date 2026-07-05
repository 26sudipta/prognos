// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $ContestsTable extends Contests with TableInfo<$ContestsTable, Contest> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ContestsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _clistIdMeta = const VerificationMeta(
    'clistId',
  );
  @override
  late final GeneratedColumn<int> clistId = GeneratedColumn<int>(
    'clist_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _platformMeta = const VerificationMeta(
    'platform',
  );
  @override
  late final GeneratedColumn<String> platform = GeneratedColumn<String>(
    'platform',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _startTimeMeta = const VerificationMeta(
    'startTime',
  );
  @override
  late final GeneratedColumn<DateTime> startTime = GeneratedColumn<DateTime>(
    'start_time',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _endTimeMeta = const VerificationMeta(
    'endTime',
  );
  @override
  late final GeneratedColumn<DateTime> endTime = GeneratedColumn<DateTime>(
    'end_time',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _durationSecondsMeta = const VerificationMeta(
    'durationSeconds',
  );
  @override
  late final GeneratedColumn<int> durationSeconds = GeneratedColumn<int>(
    'duration_seconds',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _urlMeta = const VerificationMeta('url');
  @override
  late final GeneratedColumn<String> url = GeneratedColumn<String>(
    'url',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastSyncedAtMeta = const VerificationMeta(
    'lastSyncedAt',
  );
  @override
  late final GeneratedColumn<DateTime> lastSyncedAt = GeneratedColumn<DateTime>(
    'last_synced_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _cachedAtMeta = const VerificationMeta(
    'cachedAt',
  );
  @override
  late final GeneratedColumn<DateTime> cachedAt = GeneratedColumn<DateTime>(
    'cached_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    clistId,
    platform,
    name,
    startTime,
    endTime,
    durationSeconds,
    url,
    lastSyncedAt,
    cachedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'contests';
  @override
  VerificationContext validateIntegrity(
    Insertable<Contest> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('clist_id')) {
      context.handle(
        _clistIdMeta,
        clistId.isAcceptableOrUnknown(data['clist_id']!, _clistIdMeta),
      );
    } else if (isInserting) {
      context.missing(_clistIdMeta);
    }
    if (data.containsKey('platform')) {
      context.handle(
        _platformMeta,
        platform.isAcceptableOrUnknown(data['platform']!, _platformMeta),
      );
    } else if (isInserting) {
      context.missing(_platformMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('start_time')) {
      context.handle(
        _startTimeMeta,
        startTime.isAcceptableOrUnknown(data['start_time']!, _startTimeMeta),
      );
    } else if (isInserting) {
      context.missing(_startTimeMeta);
    }
    if (data.containsKey('end_time')) {
      context.handle(
        _endTimeMeta,
        endTime.isAcceptableOrUnknown(data['end_time']!, _endTimeMeta),
      );
    } else if (isInserting) {
      context.missing(_endTimeMeta);
    }
    if (data.containsKey('duration_seconds')) {
      context.handle(
        _durationSecondsMeta,
        durationSeconds.isAcceptableOrUnknown(
          data['duration_seconds']!,
          _durationSecondsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_durationSecondsMeta);
    }
    if (data.containsKey('url')) {
      context.handle(
        _urlMeta,
        url.isAcceptableOrUnknown(data['url']!, _urlMeta),
      );
    } else if (isInserting) {
      context.missing(_urlMeta);
    }
    if (data.containsKey('last_synced_at')) {
      context.handle(
        _lastSyncedAtMeta,
        lastSyncedAt.isAcceptableOrUnknown(
          data['last_synced_at']!,
          _lastSyncedAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_lastSyncedAtMeta);
    }
    if (data.containsKey('cached_at')) {
      context.handle(
        _cachedAtMeta,
        cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_cachedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Contest map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Contest(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      clistId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}clist_id'],
      )!,
      platform: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}platform'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      startTime: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}start_time'],
      )!,
      endTime: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}end_time'],
      )!,
      durationSeconds: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}duration_seconds'],
      )!,
      url: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}url'],
      )!,
      lastSyncedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}last_synced_at'],
      )!,
      cachedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}cached_at'],
      )!,
    );
  }

  @override
  $ContestsTable createAlias(String alias) {
    return $ContestsTable(attachedDatabase, alias);
  }
}

class Contest extends DataClass implements Insertable<Contest> {
  final String id;
  final int clistId;
  final String platform;
  final String name;
  final DateTime startTime;
  final DateTime endTime;
  final int durationSeconds;
  final String url;
  final DateTime lastSyncedAt;
  final DateTime cachedAt;
  const Contest({
    required this.id,
    required this.clistId,
    required this.platform,
    required this.name,
    required this.startTime,
    required this.endTime,
    required this.durationSeconds,
    required this.url,
    required this.lastSyncedAt,
    required this.cachedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['clist_id'] = Variable<int>(clistId);
    map['platform'] = Variable<String>(platform);
    map['name'] = Variable<String>(name);
    map['start_time'] = Variable<DateTime>(startTime);
    map['end_time'] = Variable<DateTime>(endTime);
    map['duration_seconds'] = Variable<int>(durationSeconds);
    map['url'] = Variable<String>(url);
    map['last_synced_at'] = Variable<DateTime>(lastSyncedAt);
    map['cached_at'] = Variable<DateTime>(cachedAt);
    return map;
  }

  ContestsCompanion toCompanion(bool nullToAbsent) {
    return ContestsCompanion(
      id: Value(id),
      clistId: Value(clistId),
      platform: Value(platform),
      name: Value(name),
      startTime: Value(startTime),
      endTime: Value(endTime),
      durationSeconds: Value(durationSeconds),
      url: Value(url),
      lastSyncedAt: Value(lastSyncedAt),
      cachedAt: Value(cachedAt),
    );
  }

  factory Contest.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Contest(
      id: serializer.fromJson<String>(json['id']),
      clistId: serializer.fromJson<int>(json['clistId']),
      platform: serializer.fromJson<String>(json['platform']),
      name: serializer.fromJson<String>(json['name']),
      startTime: serializer.fromJson<DateTime>(json['startTime']),
      endTime: serializer.fromJson<DateTime>(json['endTime']),
      durationSeconds: serializer.fromJson<int>(json['durationSeconds']),
      url: serializer.fromJson<String>(json['url']),
      lastSyncedAt: serializer.fromJson<DateTime>(json['lastSyncedAt']),
      cachedAt: serializer.fromJson<DateTime>(json['cachedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'clistId': serializer.toJson<int>(clistId),
      'platform': serializer.toJson<String>(platform),
      'name': serializer.toJson<String>(name),
      'startTime': serializer.toJson<DateTime>(startTime),
      'endTime': serializer.toJson<DateTime>(endTime),
      'durationSeconds': serializer.toJson<int>(durationSeconds),
      'url': serializer.toJson<String>(url),
      'lastSyncedAt': serializer.toJson<DateTime>(lastSyncedAt),
      'cachedAt': serializer.toJson<DateTime>(cachedAt),
    };
  }

  Contest copyWith({
    String? id,
    int? clistId,
    String? platform,
    String? name,
    DateTime? startTime,
    DateTime? endTime,
    int? durationSeconds,
    String? url,
    DateTime? lastSyncedAt,
    DateTime? cachedAt,
  }) => Contest(
    id: id ?? this.id,
    clistId: clistId ?? this.clistId,
    platform: platform ?? this.platform,
    name: name ?? this.name,
    startTime: startTime ?? this.startTime,
    endTime: endTime ?? this.endTime,
    durationSeconds: durationSeconds ?? this.durationSeconds,
    url: url ?? this.url,
    lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
    cachedAt: cachedAt ?? this.cachedAt,
  );
  Contest copyWithCompanion(ContestsCompanion data) {
    return Contest(
      id: data.id.present ? data.id.value : this.id,
      clistId: data.clistId.present ? data.clistId.value : this.clistId,
      platform: data.platform.present ? data.platform.value : this.platform,
      name: data.name.present ? data.name.value : this.name,
      startTime: data.startTime.present ? data.startTime.value : this.startTime,
      endTime: data.endTime.present ? data.endTime.value : this.endTime,
      durationSeconds: data.durationSeconds.present
          ? data.durationSeconds.value
          : this.durationSeconds,
      url: data.url.present ? data.url.value : this.url,
      lastSyncedAt: data.lastSyncedAt.present
          ? data.lastSyncedAt.value
          : this.lastSyncedAt,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Contest(')
          ..write('id: $id, ')
          ..write('clistId: $clistId, ')
          ..write('platform: $platform, ')
          ..write('name: $name, ')
          ..write('startTime: $startTime, ')
          ..write('endTime: $endTime, ')
          ..write('durationSeconds: $durationSeconds, ')
          ..write('url: $url, ')
          ..write('lastSyncedAt: $lastSyncedAt, ')
          ..write('cachedAt: $cachedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    clistId,
    platform,
    name,
    startTime,
    endTime,
    durationSeconds,
    url,
    lastSyncedAt,
    cachedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Contest &&
          other.id == this.id &&
          other.clistId == this.clistId &&
          other.platform == this.platform &&
          other.name == this.name &&
          other.startTime == this.startTime &&
          other.endTime == this.endTime &&
          other.durationSeconds == this.durationSeconds &&
          other.url == this.url &&
          other.lastSyncedAt == this.lastSyncedAt &&
          other.cachedAt == this.cachedAt);
}

class ContestsCompanion extends UpdateCompanion<Contest> {
  final Value<String> id;
  final Value<int> clistId;
  final Value<String> platform;
  final Value<String> name;
  final Value<DateTime> startTime;
  final Value<DateTime> endTime;
  final Value<int> durationSeconds;
  final Value<String> url;
  final Value<DateTime> lastSyncedAt;
  final Value<DateTime> cachedAt;
  final Value<int> rowid;
  const ContestsCompanion({
    this.id = const Value.absent(),
    this.clistId = const Value.absent(),
    this.platform = const Value.absent(),
    this.name = const Value.absent(),
    this.startTime = const Value.absent(),
    this.endTime = const Value.absent(),
    this.durationSeconds = const Value.absent(),
    this.url = const Value.absent(),
    this.lastSyncedAt = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ContestsCompanion.insert({
    required String id,
    required int clistId,
    required String platform,
    required String name,
    required DateTime startTime,
    required DateTime endTime,
    required int durationSeconds,
    required String url,
    required DateTime lastSyncedAt,
    required DateTime cachedAt,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       clistId = Value(clistId),
       platform = Value(platform),
       name = Value(name),
       startTime = Value(startTime),
       endTime = Value(endTime),
       durationSeconds = Value(durationSeconds),
       url = Value(url),
       lastSyncedAt = Value(lastSyncedAt),
       cachedAt = Value(cachedAt);
  static Insertable<Contest> custom({
    Expression<String>? id,
    Expression<int>? clistId,
    Expression<String>? platform,
    Expression<String>? name,
    Expression<DateTime>? startTime,
    Expression<DateTime>? endTime,
    Expression<int>? durationSeconds,
    Expression<String>? url,
    Expression<DateTime>? lastSyncedAt,
    Expression<DateTime>? cachedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (clistId != null) 'clist_id': clistId,
      if (platform != null) 'platform': platform,
      if (name != null) 'name': name,
      if (startTime != null) 'start_time': startTime,
      if (endTime != null) 'end_time': endTime,
      if (durationSeconds != null) 'duration_seconds': durationSeconds,
      if (url != null) 'url': url,
      if (lastSyncedAt != null) 'last_synced_at': lastSyncedAt,
      if (cachedAt != null) 'cached_at': cachedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ContestsCompanion copyWith({
    Value<String>? id,
    Value<int>? clistId,
    Value<String>? platform,
    Value<String>? name,
    Value<DateTime>? startTime,
    Value<DateTime>? endTime,
    Value<int>? durationSeconds,
    Value<String>? url,
    Value<DateTime>? lastSyncedAt,
    Value<DateTime>? cachedAt,
    Value<int>? rowid,
  }) {
    return ContestsCompanion(
      id: id ?? this.id,
      clistId: clistId ?? this.clistId,
      platform: platform ?? this.platform,
      name: name ?? this.name,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      durationSeconds: durationSeconds ?? this.durationSeconds,
      url: url ?? this.url,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      cachedAt: cachedAt ?? this.cachedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (clistId.present) {
      map['clist_id'] = Variable<int>(clistId.value);
    }
    if (platform.present) {
      map['platform'] = Variable<String>(platform.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (startTime.present) {
      map['start_time'] = Variable<DateTime>(startTime.value);
    }
    if (endTime.present) {
      map['end_time'] = Variable<DateTime>(endTime.value);
    }
    if (durationSeconds.present) {
      map['duration_seconds'] = Variable<int>(durationSeconds.value);
    }
    if (url.present) {
      map['url'] = Variable<String>(url.value);
    }
    if (lastSyncedAt.present) {
      map['last_synced_at'] = Variable<DateTime>(lastSyncedAt.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<DateTime>(cachedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ContestsCompanion(')
          ..write('id: $id, ')
          ..write('clistId: $clistId, ')
          ..write('platform: $platform, ')
          ..write('name: $name, ')
          ..write('startTime: $startTime, ')
          ..write('endTime: $endTime, ')
          ..write('durationSeconds: $durationSeconds, ')
          ..write('url: $url, ')
          ..write('lastSyncedAt: $lastSyncedAt, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $StarredContestsTable extends StarredContests
    with TableInfo<$StarredContestsTable, StarredContest> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $StarredContestsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _contestIdMeta = const VerificationMeta(
    'contestId',
  );
  @override
  late final GeneratedColumn<String> contestId = GeneratedColumn<String>(
    'contest_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [contestId];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'starred_contests';
  @override
  VerificationContext validateIntegrity(
    Insertable<StarredContest> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('contest_id')) {
      context.handle(
        _contestIdMeta,
        contestId.isAcceptableOrUnknown(data['contest_id']!, _contestIdMeta),
      );
    } else if (isInserting) {
      context.missing(_contestIdMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {contestId};
  @override
  StarredContest map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return StarredContest(
      contestId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}contest_id'],
      )!,
    );
  }

  @override
  $StarredContestsTable createAlias(String alias) {
    return $StarredContestsTable(attachedDatabase, alias);
  }
}

class StarredContest extends DataClass implements Insertable<StarredContest> {
  final String contestId;
  const StarredContest({required this.contestId});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['contest_id'] = Variable<String>(contestId);
    return map;
  }

  StarredContestsCompanion toCompanion(bool nullToAbsent) {
    return StarredContestsCompanion(contestId: Value(contestId));
  }

  factory StarredContest.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return StarredContest(
      contestId: serializer.fromJson<String>(json['contestId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{'contestId': serializer.toJson<String>(contestId)};
  }

  StarredContest copyWith({String? contestId}) =>
      StarredContest(contestId: contestId ?? this.contestId);
  StarredContest copyWithCompanion(StarredContestsCompanion data) {
    return StarredContest(
      contestId: data.contestId.present ? data.contestId.value : this.contestId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('StarredContest(')
          ..write('contestId: $contestId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => contestId.hashCode;
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is StarredContest && other.contestId == this.contestId);
}

class StarredContestsCompanion extends UpdateCompanion<StarredContest> {
  final Value<String> contestId;
  final Value<int> rowid;
  const StarredContestsCompanion({
    this.contestId = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  StarredContestsCompanion.insert({
    required String contestId,
    this.rowid = const Value.absent(),
  }) : contestId = Value(contestId);
  static Insertable<StarredContest> custom({
    Expression<String>? contestId,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (contestId != null) 'contest_id': contestId,
      if (rowid != null) 'rowid': rowid,
    });
  }

  StarredContestsCompanion copyWith({
    Value<String>? contestId,
    Value<int>? rowid,
  }) {
    return StarredContestsCompanion(
      contestId: contestId ?? this.contestId,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (contestId.present) {
      map['contest_id'] = Variable<String>(contestId.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('StarredContestsCompanion(')
          ..write('contestId: $contestId, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $PlatformRulesTable extends PlatformRules
    with TableInfo<$PlatformRulesTable, PlatformRule> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PlatformRulesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _platformMeta = const VerificationMeta(
    'platform',
  );
  @override
  late final GeneratedColumn<String> platform = GeneratedColumn<String>(
    'platform',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _enabledMeta = const VerificationMeta(
    'enabled',
  );
  @override
  late final GeneratedColumn<bool> enabled = GeneratedColumn<bool>(
    'enabled',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("enabled" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  @override
  List<GeneratedColumn> get $columns => [platform, enabled];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'platform_rules';
  @override
  VerificationContext validateIntegrity(
    Insertable<PlatformRule> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('platform')) {
      context.handle(
        _platformMeta,
        platform.isAcceptableOrUnknown(data['platform']!, _platformMeta),
      );
    } else if (isInserting) {
      context.missing(_platformMeta);
    }
    if (data.containsKey('enabled')) {
      context.handle(
        _enabledMeta,
        enabled.isAcceptableOrUnknown(data['enabled']!, _enabledMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {platform};
  @override
  PlatformRule map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PlatformRule(
      platform: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}platform'],
      )!,
      enabled: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}enabled'],
      )!,
    );
  }

  @override
  $PlatformRulesTable createAlias(String alias) {
    return $PlatformRulesTable(attachedDatabase, alias);
  }
}

class PlatformRule extends DataClass implements Insertable<PlatformRule> {
  final String platform;
  final bool enabled;
  const PlatformRule({required this.platform, required this.enabled});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['platform'] = Variable<String>(platform);
    map['enabled'] = Variable<bool>(enabled);
    return map;
  }

  PlatformRulesCompanion toCompanion(bool nullToAbsent) {
    return PlatformRulesCompanion(
      platform: Value(platform),
      enabled: Value(enabled),
    );
  }

  factory PlatformRule.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PlatformRule(
      platform: serializer.fromJson<String>(json['platform']),
      enabled: serializer.fromJson<bool>(json['enabled']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'platform': serializer.toJson<String>(platform),
      'enabled': serializer.toJson<bool>(enabled),
    };
  }

  PlatformRule copyWith({String? platform, bool? enabled}) => PlatformRule(
    platform: platform ?? this.platform,
    enabled: enabled ?? this.enabled,
  );
  PlatformRule copyWithCompanion(PlatformRulesCompanion data) {
    return PlatformRule(
      platform: data.platform.present ? data.platform.value : this.platform,
      enabled: data.enabled.present ? data.enabled.value : this.enabled,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PlatformRule(')
          ..write('platform: $platform, ')
          ..write('enabled: $enabled')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(platform, enabled);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PlatformRule &&
          other.platform == this.platform &&
          other.enabled == this.enabled);
}

class PlatformRulesCompanion extends UpdateCompanion<PlatformRule> {
  final Value<String> platform;
  final Value<bool> enabled;
  final Value<int> rowid;
  const PlatformRulesCompanion({
    this.platform = const Value.absent(),
    this.enabled = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  PlatformRulesCompanion.insert({
    required String platform,
    this.enabled = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : platform = Value(platform);
  static Insertable<PlatformRule> custom({
    Expression<String>? platform,
    Expression<bool>? enabled,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (platform != null) 'platform': platform,
      if (enabled != null) 'enabled': enabled,
      if (rowid != null) 'rowid': rowid,
    });
  }

  PlatformRulesCompanion copyWith({
    Value<String>? platform,
    Value<bool>? enabled,
    Value<int>? rowid,
  }) {
    return PlatformRulesCompanion(
      platform: platform ?? this.platform,
      enabled: enabled ?? this.enabled,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (platform.present) {
      map['platform'] = Variable<String>(platform.value);
    }
    if (enabled.present) {
      map['enabled'] = Variable<bool>(enabled.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PlatformRulesCompanion(')
          ..write('platform: $platform, ')
          ..write('enabled: $enabled, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ScheduledRemindersTable extends ScheduledReminders
    with TableInfo<$ScheduledRemindersTable, ScheduledReminder> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ScheduledRemindersTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _notifIdMeta = const VerificationMeta(
    'notifId',
  );
  @override
  late final GeneratedColumn<int> notifId = GeneratedColumn<int>(
    'notif_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _contestIdMeta = const VerificationMeta(
    'contestId',
  );
  @override
  late final GeneratedColumn<String> contestId = GeneratedColumn<String>(
    'contest_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _leadMinutesMeta = const VerificationMeta(
    'leadMinutes',
  );
  @override
  late final GeneratedColumn<int> leadMinutes = GeneratedColumn<int>(
    'lead_minutes',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fireAtMeta = const VerificationMeta('fireAt');
  @override
  late final GeneratedColumn<DateTime> fireAt = GeneratedColumn<DateTime>(
    'fire_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    notifId,
    contestId,
    leadMinutes,
    fireAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'scheduled_reminders';
  @override
  VerificationContext validateIntegrity(
    Insertable<ScheduledReminder> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('notif_id')) {
      context.handle(
        _notifIdMeta,
        notifId.isAcceptableOrUnknown(data['notif_id']!, _notifIdMeta),
      );
    }
    if (data.containsKey('contest_id')) {
      context.handle(
        _contestIdMeta,
        contestId.isAcceptableOrUnknown(data['contest_id']!, _contestIdMeta),
      );
    } else if (isInserting) {
      context.missing(_contestIdMeta);
    }
    if (data.containsKey('lead_minutes')) {
      context.handle(
        _leadMinutesMeta,
        leadMinutes.isAcceptableOrUnknown(
          data['lead_minutes']!,
          _leadMinutesMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_leadMinutesMeta);
    }
    if (data.containsKey('fire_at')) {
      context.handle(
        _fireAtMeta,
        fireAt.isAcceptableOrUnknown(data['fire_at']!, _fireAtMeta),
      );
    } else if (isInserting) {
      context.missing(_fireAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {notifId};
  @override
  ScheduledReminder map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ScheduledReminder(
      notifId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}notif_id'],
      )!,
      contestId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}contest_id'],
      )!,
      leadMinutes: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}lead_minutes'],
      )!,
      fireAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}fire_at'],
      )!,
    );
  }

  @override
  $ScheduledRemindersTable createAlias(String alias) {
    return $ScheduledRemindersTable(attachedDatabase, alias);
  }
}

class ScheduledReminder extends DataClass
    implements Insertable<ScheduledReminder> {
  final int notifId;
  final String contestId;
  final int leadMinutes;
  final DateTime fireAt;
  const ScheduledReminder({
    required this.notifId,
    required this.contestId,
    required this.leadMinutes,
    required this.fireAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['notif_id'] = Variable<int>(notifId);
    map['contest_id'] = Variable<String>(contestId);
    map['lead_minutes'] = Variable<int>(leadMinutes);
    map['fire_at'] = Variable<DateTime>(fireAt);
    return map;
  }

  ScheduledRemindersCompanion toCompanion(bool nullToAbsent) {
    return ScheduledRemindersCompanion(
      notifId: Value(notifId),
      contestId: Value(contestId),
      leadMinutes: Value(leadMinutes),
      fireAt: Value(fireAt),
    );
  }

  factory ScheduledReminder.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ScheduledReminder(
      notifId: serializer.fromJson<int>(json['notifId']),
      contestId: serializer.fromJson<String>(json['contestId']),
      leadMinutes: serializer.fromJson<int>(json['leadMinutes']),
      fireAt: serializer.fromJson<DateTime>(json['fireAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'notifId': serializer.toJson<int>(notifId),
      'contestId': serializer.toJson<String>(contestId),
      'leadMinutes': serializer.toJson<int>(leadMinutes),
      'fireAt': serializer.toJson<DateTime>(fireAt),
    };
  }

  ScheduledReminder copyWith({
    int? notifId,
    String? contestId,
    int? leadMinutes,
    DateTime? fireAt,
  }) => ScheduledReminder(
    notifId: notifId ?? this.notifId,
    contestId: contestId ?? this.contestId,
    leadMinutes: leadMinutes ?? this.leadMinutes,
    fireAt: fireAt ?? this.fireAt,
  );
  ScheduledReminder copyWithCompanion(ScheduledRemindersCompanion data) {
    return ScheduledReminder(
      notifId: data.notifId.present ? data.notifId.value : this.notifId,
      contestId: data.contestId.present ? data.contestId.value : this.contestId,
      leadMinutes: data.leadMinutes.present
          ? data.leadMinutes.value
          : this.leadMinutes,
      fireAt: data.fireAt.present ? data.fireAt.value : this.fireAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ScheduledReminder(')
          ..write('notifId: $notifId, ')
          ..write('contestId: $contestId, ')
          ..write('leadMinutes: $leadMinutes, ')
          ..write('fireAt: $fireAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(notifId, contestId, leadMinutes, fireAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ScheduledReminder &&
          other.notifId == this.notifId &&
          other.contestId == this.contestId &&
          other.leadMinutes == this.leadMinutes &&
          other.fireAt == this.fireAt);
}

class ScheduledRemindersCompanion extends UpdateCompanion<ScheduledReminder> {
  final Value<int> notifId;
  final Value<String> contestId;
  final Value<int> leadMinutes;
  final Value<DateTime> fireAt;
  const ScheduledRemindersCompanion({
    this.notifId = const Value.absent(),
    this.contestId = const Value.absent(),
    this.leadMinutes = const Value.absent(),
    this.fireAt = const Value.absent(),
  });
  ScheduledRemindersCompanion.insert({
    this.notifId = const Value.absent(),
    required String contestId,
    required int leadMinutes,
    required DateTime fireAt,
  }) : contestId = Value(contestId),
       leadMinutes = Value(leadMinutes),
       fireAt = Value(fireAt);
  static Insertable<ScheduledReminder> custom({
    Expression<int>? notifId,
    Expression<String>? contestId,
    Expression<int>? leadMinutes,
    Expression<DateTime>? fireAt,
  }) {
    return RawValuesInsertable({
      if (notifId != null) 'notif_id': notifId,
      if (contestId != null) 'contest_id': contestId,
      if (leadMinutes != null) 'lead_minutes': leadMinutes,
      if (fireAt != null) 'fire_at': fireAt,
    });
  }

  ScheduledRemindersCompanion copyWith({
    Value<int>? notifId,
    Value<String>? contestId,
    Value<int>? leadMinutes,
    Value<DateTime>? fireAt,
  }) {
    return ScheduledRemindersCompanion(
      notifId: notifId ?? this.notifId,
      contestId: contestId ?? this.contestId,
      leadMinutes: leadMinutes ?? this.leadMinutes,
      fireAt: fireAt ?? this.fireAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (notifId.present) {
      map['notif_id'] = Variable<int>(notifId.value);
    }
    if (contestId.present) {
      map['contest_id'] = Variable<String>(contestId.value);
    }
    if (leadMinutes.present) {
      map['lead_minutes'] = Variable<int>(leadMinutes.value);
    }
    if (fireAt.present) {
      map['fire_at'] = Variable<DateTime>(fireAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ScheduledRemindersCompanion(')
          ..write('notifId: $notifId, ')
          ..write('contestId: $contestId, ')
          ..write('leadMinutes: $leadMinutes, ')
          ..write('fireAt: $fireAt')
          ..write(')'))
        .toString();
  }
}

class $SettingsTable extends Settings with TableInfo<$SettingsTable, Setting> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SettingsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
    'key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
    'value',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'settings';
  @override
  VerificationContext validateIntegrity(
    Insertable<Setting> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
        _keyMeta,
        key.isAcceptableOrUnknown(data['key']!, _keyMeta),
      );
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
        _valueMeta,
        value.isAcceptableOrUnknown(data['value']!, _valueMeta),
      );
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  Setting map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Setting(
      key: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}key'],
      )!,
      value: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}value'],
      )!,
    );
  }

  @override
  $SettingsTable createAlias(String alias) {
    return $SettingsTable(attachedDatabase, alias);
  }
}

class Setting extends DataClass implements Insertable<Setting> {
  final String key;
  final String value;
  const Setting({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  SettingsCompanion toCompanion(bool nullToAbsent) {
    return SettingsCompanion(key: Value(key), value: Value(value));
  }

  factory Setting.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Setting(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  Setting copyWith({String? key, String? value}) =>
      Setting(key: key ?? this.key, value: value ?? this.value);
  Setting copyWithCompanion(SettingsCompanion data) {
    return Setting(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Setting(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Setting && other.key == this.key && other.value == this.value);
}

class SettingsCompanion extends UpdateCompanion<Setting> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const SettingsCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SettingsCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  }) : key = Value(key),
       value = Value(value);
  static Insertable<Setting> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SettingsCompanion copyWith({
    Value<String>? key,
    Value<String>? value,
    Value<int>? rowid,
  }) {
    return SettingsCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SettingsCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $ContestsTable contests = $ContestsTable(this);
  late final $StarredContestsTable starredContests = $StarredContestsTable(
    this,
  );
  late final $PlatformRulesTable platformRules = $PlatformRulesTable(this);
  late final $ScheduledRemindersTable scheduledReminders =
      $ScheduledRemindersTable(this);
  late final $SettingsTable settings = $SettingsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    contests,
    starredContests,
    platformRules,
    scheduledReminders,
    settings,
  ];
}

typedef $$ContestsTableCreateCompanionBuilder =
    ContestsCompanion Function({
      required String id,
      required int clistId,
      required String platform,
      required String name,
      required DateTime startTime,
      required DateTime endTime,
      required int durationSeconds,
      required String url,
      required DateTime lastSyncedAt,
      required DateTime cachedAt,
      Value<int> rowid,
    });
typedef $$ContestsTableUpdateCompanionBuilder =
    ContestsCompanion Function({
      Value<String> id,
      Value<int> clistId,
      Value<String> platform,
      Value<String> name,
      Value<DateTime> startTime,
      Value<DateTime> endTime,
      Value<int> durationSeconds,
      Value<String> url,
      Value<DateTime> lastSyncedAt,
      Value<DateTime> cachedAt,
      Value<int> rowid,
    });

class $$ContestsTableFilterComposer
    extends Composer<_$AppDatabase, $ContestsTable> {
  $$ContestsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get clistId => $composableBuilder(
    column: $table.clistId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get platform => $composableBuilder(
    column: $table.platform,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get startTime => $composableBuilder(
    column: $table.startTime,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get endTime => $composableBuilder(
    column: $table.endTime,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get durationSeconds => $composableBuilder(
    column: $table.durationSeconds,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get url => $composableBuilder(
    column: $table.url,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get cachedAt => $composableBuilder(
    column: $table.cachedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ContestsTableOrderingComposer
    extends Composer<_$AppDatabase, $ContestsTable> {
  $$ContestsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get clistId => $composableBuilder(
    column: $table.clistId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get platform => $composableBuilder(
    column: $table.platform,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get startTime => $composableBuilder(
    column: $table.startTime,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get endTime => $composableBuilder(
    column: $table.endTime,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get durationSeconds => $composableBuilder(
    column: $table.durationSeconds,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get url => $composableBuilder(
    column: $table.url,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get cachedAt => $composableBuilder(
    column: $table.cachedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ContestsTableAnnotationComposer
    extends Composer<_$AppDatabase, $ContestsTable> {
  $$ContestsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<int> get clistId =>
      $composableBuilder(column: $table.clistId, builder: (column) => column);

  GeneratedColumn<String> get platform =>
      $composableBuilder(column: $table.platform, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<DateTime> get startTime =>
      $composableBuilder(column: $table.startTime, builder: (column) => column);

  GeneratedColumn<DateTime> get endTime =>
      $composableBuilder(column: $table.endTime, builder: (column) => column);

  GeneratedColumn<int> get durationSeconds => $composableBuilder(
    column: $table.durationSeconds,
    builder: (column) => column,
  );

  GeneratedColumn<String> get url =>
      $composableBuilder(column: $table.url, builder: (column) => column);

  GeneratedColumn<DateTime> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);
}

class $$ContestsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ContestsTable,
          Contest,
          $$ContestsTableFilterComposer,
          $$ContestsTableOrderingComposer,
          $$ContestsTableAnnotationComposer,
          $$ContestsTableCreateCompanionBuilder,
          $$ContestsTableUpdateCompanionBuilder,
          (Contest, BaseReferences<_$AppDatabase, $ContestsTable, Contest>),
          Contest,
          PrefetchHooks Function()
        > {
  $$ContestsTableTableManager(_$AppDatabase db, $ContestsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ContestsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ContestsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ContestsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<int> clistId = const Value.absent(),
                Value<String> platform = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<DateTime> startTime = const Value.absent(),
                Value<DateTime> endTime = const Value.absent(),
                Value<int> durationSeconds = const Value.absent(),
                Value<String> url = const Value.absent(),
                Value<DateTime> lastSyncedAt = const Value.absent(),
                Value<DateTime> cachedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ContestsCompanion(
                id: id,
                clistId: clistId,
                platform: platform,
                name: name,
                startTime: startTime,
                endTime: endTime,
                durationSeconds: durationSeconds,
                url: url,
                lastSyncedAt: lastSyncedAt,
                cachedAt: cachedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required int clistId,
                required String platform,
                required String name,
                required DateTime startTime,
                required DateTime endTime,
                required int durationSeconds,
                required String url,
                required DateTime lastSyncedAt,
                required DateTime cachedAt,
                Value<int> rowid = const Value.absent(),
              }) => ContestsCompanion.insert(
                id: id,
                clistId: clistId,
                platform: platform,
                name: name,
                startTime: startTime,
                endTime: endTime,
                durationSeconds: durationSeconds,
                url: url,
                lastSyncedAt: lastSyncedAt,
                cachedAt: cachedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ContestsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ContestsTable,
      Contest,
      $$ContestsTableFilterComposer,
      $$ContestsTableOrderingComposer,
      $$ContestsTableAnnotationComposer,
      $$ContestsTableCreateCompanionBuilder,
      $$ContestsTableUpdateCompanionBuilder,
      (Contest, BaseReferences<_$AppDatabase, $ContestsTable, Contest>),
      Contest,
      PrefetchHooks Function()
    >;
typedef $$StarredContestsTableCreateCompanionBuilder =
    StarredContestsCompanion Function({
      required String contestId,
      Value<int> rowid,
    });
typedef $$StarredContestsTableUpdateCompanionBuilder =
    StarredContestsCompanion Function({
      Value<String> contestId,
      Value<int> rowid,
    });

class $$StarredContestsTableFilterComposer
    extends Composer<_$AppDatabase, $StarredContestsTable> {
  $$StarredContestsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get contestId => $composableBuilder(
    column: $table.contestId,
    builder: (column) => ColumnFilters(column),
  );
}

class $$StarredContestsTableOrderingComposer
    extends Composer<_$AppDatabase, $StarredContestsTable> {
  $$StarredContestsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get contestId => $composableBuilder(
    column: $table.contestId,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$StarredContestsTableAnnotationComposer
    extends Composer<_$AppDatabase, $StarredContestsTable> {
  $$StarredContestsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get contestId =>
      $composableBuilder(column: $table.contestId, builder: (column) => column);
}

class $$StarredContestsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $StarredContestsTable,
          StarredContest,
          $$StarredContestsTableFilterComposer,
          $$StarredContestsTableOrderingComposer,
          $$StarredContestsTableAnnotationComposer,
          $$StarredContestsTableCreateCompanionBuilder,
          $$StarredContestsTableUpdateCompanionBuilder,
          (
            StarredContest,
            BaseReferences<
              _$AppDatabase,
              $StarredContestsTable,
              StarredContest
            >,
          ),
          StarredContest,
          PrefetchHooks Function()
        > {
  $$StarredContestsTableTableManager(
    _$AppDatabase db,
    $StarredContestsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$StarredContestsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$StarredContestsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$StarredContestsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> contestId = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) =>
                  StarredContestsCompanion(contestId: contestId, rowid: rowid),
          createCompanionCallback:
              ({
                required String contestId,
                Value<int> rowid = const Value.absent(),
              }) => StarredContestsCompanion.insert(
                contestId: contestId,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$StarredContestsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $StarredContestsTable,
      StarredContest,
      $$StarredContestsTableFilterComposer,
      $$StarredContestsTableOrderingComposer,
      $$StarredContestsTableAnnotationComposer,
      $$StarredContestsTableCreateCompanionBuilder,
      $$StarredContestsTableUpdateCompanionBuilder,
      (
        StarredContest,
        BaseReferences<_$AppDatabase, $StarredContestsTable, StarredContest>,
      ),
      StarredContest,
      PrefetchHooks Function()
    >;
typedef $$PlatformRulesTableCreateCompanionBuilder =
    PlatformRulesCompanion Function({
      required String platform,
      Value<bool> enabled,
      Value<int> rowid,
    });
typedef $$PlatformRulesTableUpdateCompanionBuilder =
    PlatformRulesCompanion Function({
      Value<String> platform,
      Value<bool> enabled,
      Value<int> rowid,
    });

class $$PlatformRulesTableFilterComposer
    extends Composer<_$AppDatabase, $PlatformRulesTable> {
  $$PlatformRulesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get platform => $composableBuilder(
    column: $table.platform,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get enabled => $composableBuilder(
    column: $table.enabled,
    builder: (column) => ColumnFilters(column),
  );
}

class $$PlatformRulesTableOrderingComposer
    extends Composer<_$AppDatabase, $PlatformRulesTable> {
  $$PlatformRulesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get platform => $composableBuilder(
    column: $table.platform,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get enabled => $composableBuilder(
    column: $table.enabled,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$PlatformRulesTableAnnotationComposer
    extends Composer<_$AppDatabase, $PlatformRulesTable> {
  $$PlatformRulesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get platform =>
      $composableBuilder(column: $table.platform, builder: (column) => column);

  GeneratedColumn<bool> get enabled =>
      $composableBuilder(column: $table.enabled, builder: (column) => column);
}

class $$PlatformRulesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $PlatformRulesTable,
          PlatformRule,
          $$PlatformRulesTableFilterComposer,
          $$PlatformRulesTableOrderingComposer,
          $$PlatformRulesTableAnnotationComposer,
          $$PlatformRulesTableCreateCompanionBuilder,
          $$PlatformRulesTableUpdateCompanionBuilder,
          (
            PlatformRule,
            BaseReferences<_$AppDatabase, $PlatformRulesTable, PlatformRule>,
          ),
          PlatformRule,
          PrefetchHooks Function()
        > {
  $$PlatformRulesTableTableManager(_$AppDatabase db, $PlatformRulesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PlatformRulesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PlatformRulesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PlatformRulesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> platform = const Value.absent(),
                Value<bool> enabled = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => PlatformRulesCompanion(
                platform: platform,
                enabled: enabled,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String platform,
                Value<bool> enabled = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => PlatformRulesCompanion.insert(
                platform: platform,
                enabled: enabled,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$PlatformRulesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $PlatformRulesTable,
      PlatformRule,
      $$PlatformRulesTableFilterComposer,
      $$PlatformRulesTableOrderingComposer,
      $$PlatformRulesTableAnnotationComposer,
      $$PlatformRulesTableCreateCompanionBuilder,
      $$PlatformRulesTableUpdateCompanionBuilder,
      (
        PlatformRule,
        BaseReferences<_$AppDatabase, $PlatformRulesTable, PlatformRule>,
      ),
      PlatformRule,
      PrefetchHooks Function()
    >;
typedef $$ScheduledRemindersTableCreateCompanionBuilder =
    ScheduledRemindersCompanion Function({
      Value<int> notifId,
      required String contestId,
      required int leadMinutes,
      required DateTime fireAt,
    });
typedef $$ScheduledRemindersTableUpdateCompanionBuilder =
    ScheduledRemindersCompanion Function({
      Value<int> notifId,
      Value<String> contestId,
      Value<int> leadMinutes,
      Value<DateTime> fireAt,
    });

class $$ScheduledRemindersTableFilterComposer
    extends Composer<_$AppDatabase, $ScheduledRemindersTable> {
  $$ScheduledRemindersTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get notifId => $composableBuilder(
    column: $table.notifId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get contestId => $composableBuilder(
    column: $table.contestId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get leadMinutes => $composableBuilder(
    column: $table.leadMinutes,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get fireAt => $composableBuilder(
    column: $table.fireAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ScheduledRemindersTableOrderingComposer
    extends Composer<_$AppDatabase, $ScheduledRemindersTable> {
  $$ScheduledRemindersTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get notifId => $composableBuilder(
    column: $table.notifId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get contestId => $composableBuilder(
    column: $table.contestId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get leadMinutes => $composableBuilder(
    column: $table.leadMinutes,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get fireAt => $composableBuilder(
    column: $table.fireAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ScheduledRemindersTableAnnotationComposer
    extends Composer<_$AppDatabase, $ScheduledRemindersTable> {
  $$ScheduledRemindersTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get notifId =>
      $composableBuilder(column: $table.notifId, builder: (column) => column);

  GeneratedColumn<String> get contestId =>
      $composableBuilder(column: $table.contestId, builder: (column) => column);

  GeneratedColumn<int> get leadMinutes => $composableBuilder(
    column: $table.leadMinutes,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get fireAt =>
      $composableBuilder(column: $table.fireAt, builder: (column) => column);
}

class $$ScheduledRemindersTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ScheduledRemindersTable,
          ScheduledReminder,
          $$ScheduledRemindersTableFilterComposer,
          $$ScheduledRemindersTableOrderingComposer,
          $$ScheduledRemindersTableAnnotationComposer,
          $$ScheduledRemindersTableCreateCompanionBuilder,
          $$ScheduledRemindersTableUpdateCompanionBuilder,
          (
            ScheduledReminder,
            BaseReferences<
              _$AppDatabase,
              $ScheduledRemindersTable,
              ScheduledReminder
            >,
          ),
          ScheduledReminder,
          PrefetchHooks Function()
        > {
  $$ScheduledRemindersTableTableManager(
    _$AppDatabase db,
    $ScheduledRemindersTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ScheduledRemindersTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ScheduledRemindersTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ScheduledRemindersTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<int> notifId = const Value.absent(),
                Value<String> contestId = const Value.absent(),
                Value<int> leadMinutes = const Value.absent(),
                Value<DateTime> fireAt = const Value.absent(),
              }) => ScheduledRemindersCompanion(
                notifId: notifId,
                contestId: contestId,
                leadMinutes: leadMinutes,
                fireAt: fireAt,
              ),
          createCompanionCallback:
              ({
                Value<int> notifId = const Value.absent(),
                required String contestId,
                required int leadMinutes,
                required DateTime fireAt,
              }) => ScheduledRemindersCompanion.insert(
                notifId: notifId,
                contestId: contestId,
                leadMinutes: leadMinutes,
                fireAt: fireAt,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ScheduledRemindersTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ScheduledRemindersTable,
      ScheduledReminder,
      $$ScheduledRemindersTableFilterComposer,
      $$ScheduledRemindersTableOrderingComposer,
      $$ScheduledRemindersTableAnnotationComposer,
      $$ScheduledRemindersTableCreateCompanionBuilder,
      $$ScheduledRemindersTableUpdateCompanionBuilder,
      (
        ScheduledReminder,
        BaseReferences<
          _$AppDatabase,
          $ScheduledRemindersTable,
          ScheduledReminder
        >,
      ),
      ScheduledReminder,
      PrefetchHooks Function()
    >;
typedef $$SettingsTableCreateCompanionBuilder =
    SettingsCompanion Function({
      required String key,
      required String value,
      Value<int> rowid,
    });
typedef $$SettingsTableUpdateCompanionBuilder =
    SettingsCompanion Function({
      Value<String> key,
      Value<String> value,
      Value<int> rowid,
    });

class $$SettingsTableFilterComposer
    extends Composer<_$AppDatabase, $SettingsTable> {
  $$SettingsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SettingsTableOrderingComposer
    extends Composer<_$AppDatabase, $SettingsTable> {
  $$SettingsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SettingsTableAnnotationComposer
    extends Composer<_$AppDatabase, $SettingsTable> {
  $$SettingsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$SettingsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SettingsTable,
          Setting,
          $$SettingsTableFilterComposer,
          $$SettingsTableOrderingComposer,
          $$SettingsTableAnnotationComposer,
          $$SettingsTableCreateCompanionBuilder,
          $$SettingsTableUpdateCompanionBuilder,
          (Setting, BaseReferences<_$AppDatabase, $SettingsTable, Setting>),
          Setting,
          PrefetchHooks Function()
        > {
  $$SettingsTableTableManager(_$AppDatabase db, $SettingsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SettingsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SettingsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SettingsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> key = const Value.absent(),
                Value<String> value = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SettingsCompanion(key: key, value: value, rowid: rowid),
          createCompanionCallback:
              ({
                required String key,
                required String value,
                Value<int> rowid = const Value.absent(),
              }) => SettingsCompanion.insert(
                key: key,
                value: value,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SettingsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SettingsTable,
      Setting,
      $$SettingsTableFilterComposer,
      $$SettingsTableOrderingComposer,
      $$SettingsTableAnnotationComposer,
      $$SettingsTableCreateCompanionBuilder,
      $$SettingsTableUpdateCompanionBuilder,
      (Setting, BaseReferences<_$AppDatabase, $SettingsTable, Setting>),
      Setting,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$ContestsTableTableManager get contests =>
      $$ContestsTableTableManager(_db, _db.contests);
  $$StarredContestsTableTableManager get starredContests =>
      $$StarredContestsTableTableManager(_db, _db.starredContests);
  $$PlatformRulesTableTableManager get platformRules =>
      $$PlatformRulesTableTableManager(_db, _db.platformRules);
  $$ScheduledRemindersTableTableManager get scheduledReminders =>
      $$ScheduledRemindersTableTableManager(_db, _db.scheduledReminders);
  $$SettingsTableTableManager get settings =>
      $$SettingsTableTableManager(_db, _db.settings);
}
