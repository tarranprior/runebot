#! /usr/bin/env python3

import json
import sqlite3
from typing import Any

DEFAULT_SOURCE = 'bot'
LEVEL_COUNT_KEYS = ('DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR')


def _normalize_filter(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _parse_level_filters(level: str | None) -> list[str]:
    normalized_level = _normalize_filter(level)
    if not normalized_level:
        return []

    parsed_levels = [part.strip().upper() for part in normalized_level.split(',')]
    return [item for item in parsed_levels if item]


def _build_internal_logs_filters(
    level: str | None,
    module: str | None,
    search: str | None,
    source: str | None,
    session_id: str | None,
    include_level: bool,
) -> tuple[str, list[Any], str | None]:
    normalized_levels = _parse_level_filters(level)
    normalized_module = _normalize_filter(module)
    normalized_search = _normalize_filter(search)
    normalized_source = _normalize_filter(source)
    normalized_session_id = _normalize_filter(session_id)

    filters: list[str] = []
    params: list[Any] = []

    if include_level and normalized_levels:
        if len(normalized_levels) == 1:
            filters.append('level = ?')
            params.append(normalized_levels[0])
        else:
            placeholders = ','.join(['?'] * len(normalized_levels))
            filters.append(f'level IN ({placeholders})')
            params.extend(normalized_levels)
    if normalized_module:
        filters.append('module = ?')
        params.append(normalized_module)
    if normalized_source:
        filters.append('source = ?')
        params.append(normalized_source)
    if normalized_session_id:
        filters.append('session_id = ?')
        params.append(normalized_session_id)
    if normalized_search:
        filters.append('message LIKE ?')
        params.append(f'%{normalized_search}%')

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ''
    return where_clause, params, normalized_levels[0] if normalized_levels else None


def ensure_internal_logs_schema(db_path: str) -> None:
    with sqlite3.connect(db_path, timeout=5) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS log_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                started_at TEXT NOT NULL,
                log_file TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'bot'
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS internal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                logger TEXT,
                module TEXT,
                function TEXT,
                line INTEGER,
                message TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'bot',
                metadata TEXT,
                exception TEXT,
                session_id TEXT,
                trace_id TEXT
            )
            '''
        )
        try:
            conn.execute('ALTER TABLE internal_logs ADD COLUMN session_id TEXT')
        except Exception:
            pass
        try:
            conn.execute('ALTER TABLE internal_logs ADD COLUMN trace_id TEXT')
        except Exception:
            pass
        
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_trace_id ON internal_logs(trace_id)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_timestamp ON internal_logs(timestamp DESC)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_level ON internal_logs(level)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_module ON internal_logs(module)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_source ON internal_logs(source)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_session_id ON internal_logs(session_id)'
        )
        conn.commit()


def create_log_session(
    db_path: str,
    session_id: str,
    started_at: str,
    log_file: str,
    source: str = DEFAULT_SOURCE,
) -> None:
    with sqlite3.connect(db_path, timeout=5) as conn:
        conn.execute(
            'INSERT INTO log_sessions (session_id, started_at, log_file, source) VALUES (?, ?, ?, ?)',
            (session_id, started_at, log_file, source),
        )
        conn.commit()


def _validate_string_field(payload: dict[str, Any], field: str, required: bool = False) -> str | None:
    value = payload.get(field)
    if value is None:
        if required:
            raise ValueError(f'{field} is required and must be a non-empty string')
        return None

    if not isinstance(value, str):
        raise ValueError(f'{field} must be a string')

    normalized = value.strip()
    if required and not normalized:
        raise ValueError(f'{field} is required and must be a non-empty string')

    return normalized or None


def normalize_log_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError('each log item must be a JSON object')

    timestamp = _validate_string_field(payload, 'timestamp', required=True)
    level = _validate_string_field(payload, 'level', required=True)
    logger_name = _validate_string_field(payload, 'logger')
    module = _validate_string_field(payload, 'module')
    function_name = _validate_string_field(payload, 'function')
    message = _validate_string_field(payload, 'message', required=True)
    source = _validate_string_field(payload, 'source') or DEFAULT_SOURCE
    session_id = _validate_string_field(payload, 'session_id')
    trace_id = _validate_string_field(payload, 'trace_id')

    line = payload.get('line')
    if line is not None and (not isinstance(line, int) or isinstance(line, bool)):
        raise ValueError('line must be an integer')

    metadata = payload.get('metadata', {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValueError('metadata must be a JSON object')

    exception_data = payload.get('exception')
    if exception_data is not None:
        if not isinstance(exception_data, dict):
            raise ValueError('exception must be null or a JSON object')

        for exception_key in ('type', 'message', 'traceback'):
            if exception_key in exception_data and exception_data[exception_key] is not None:
                if not isinstance(exception_data[exception_key], str):
                    raise ValueError(f'exception.{exception_key} must be a string')

    return {
        'timestamp': timestamp,
        'level': level,
        'logger': logger_name,
        'module': module,
        'function': function_name,
        'line': line,
        'message': message,
        'source': source,
        'session_id': session_id,
        'trace_id': trace_id,
        'metadata': metadata,
        'exception': exception_data,
    }


def insert_internal_logs(db_path: str, logs: list[dict[str, Any]]) -> int:
    if not logs:
        return 0

    with sqlite3.connect(db_path, timeout=5) as conn:
        conn.executemany(
            '''
            INSERT INTO internal_logs (
                timestamp,
                level,
                logger,
                module,
                function,
                line,
                message,
                source,
                metadata,
                exception,
                session_id,
                trace_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            [
                (
                    item['timestamp'],
                    item['level'],
                    item['logger'],
                    item['module'],
                    item['function'],
                    item['line'],
                    item['message'],
                    item['source'],
                    json.dumps(item['metadata'], separators=(',', ':')),
                    json.dumps(item['exception'], separators=(',', ':')) if item['exception'] is not None else None,
                    item.get('session_id'),
                    item.get('trace_id'),
                )
                for item in logs
            ],
        )
        conn.commit()

    return len(logs)


def query_internal_logs(
    db_path: str,
    page: int,
    page_size: int,
    level: str | None,
    module: str | None,
    search: str | None,
    source: str | None,
    session_id: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    where_clause, params, _ = _build_internal_logs_filters(
        level=level,
        module=module,
        search=search,
        source=source,
        session_id=session_id,
        include_level=True,
    )

    count_sql = f'SELECT COUNT(*) FROM internal_logs {where_clause}'
    data_sql = (
        'SELECT id, timestamp, level, logger, module, function, line, message, source, metadata, exception, session_id, trace_id '
        f'FROM internal_logs {where_clause} '
        'ORDER BY timestamp DESC, id DESC '
        'LIMIT ? OFFSET ?'
    )

    offset = (page - 1) * page_size

    with sqlite3.connect(db_path, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute(count_sql, params).fetchone()[0]
        rows = conn.execute(data_sql, [*params, page_size, offset]).fetchall()

    items = [
        {
            'id': row['id'],
            'timestamp': row['timestamp'],
            'level': row['level'],
            'logger': row['logger'],
            'module': row['module'],
            'function': row['function'],
            'line': row['line'],
            'message': row['message'],
            'source': row['source'],
            'session_id': row['session_id'],
            'trace_id': row['trace_id'],
            'metadata': json.loads(row['metadata']) if row['metadata'] else {},
            'exception': json.loads(row['exception']) if row['exception'] else None,
        }
        for row in rows
    ]

    return items, total


def query_internal_log_level_counts(
    db_path: str,
    level: str | None,
    module: str | None,
    search: str | None,
    source: str | None,
    session_id: str | None = None,
) -> dict[str, int]:
    where_clause, params, _ = _build_internal_logs_filters(
        level=level,
        module=module,
        search=search,
        source=source,
        session_id=session_id,
        include_level=True,
    )

    sql = (
        'SELECT level, COUNT(*) AS count '
        f'FROM internal_logs {where_clause} '
        'GROUP BY level'
    )

    counts: dict[str, int] = {level_key: 0 for level_key in LEVEL_COUNT_KEYS}

    with sqlite3.connect(db_path, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()

    for row in rows:
        level_name = str(row['level']).upper()
        if level_name in counts:
            counts[level_name] = int(row['count'])

    return counts


def query_log_sessions(db_path: str) -> list[dict[str, Any]]:
    sql = (
        'SELECT ls.session_id, ls.started_at, ls.log_file, ls.source, '
        'COUNT(il.id) AS log_count '
        'FROM log_sessions ls '
        'LEFT JOIN internal_logs il ON il.session_id = ls.session_id '
        'GROUP BY ls.id '
        'ORDER BY ls.started_at DESC'
    )
    with sqlite3.connect(db_path, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchall()
    return [
        {
            'session_id': row['session_id'],
            'started_at': row['started_at'],
            'log_file': row['log_file'],
            'source': row['source'],
            'log_count': row['log_count'],
        }
        for row in rows
    ]
