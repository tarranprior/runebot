#! /usr/bin/env python3

'''
This module contains SQLite storage and query helpers for Runebot
internal logs.

Functions:
    - `ensure_internal_logs_schema()`:
            A function which ensures internal log and session tables
            and indexes exist in the database.
    - `create_log_session()`:
            A function which inserts a new log session record.
    - `normalize_log_payload()`:
            A function which validates and normalises a single internal
            log payload item.
    - `insert_internal_logs()`:
            A function which inserts normalised internal log items
            into storage.
    - `query_internal_logs()`:
            A function which queries internal logs with pagination
            and optional filters.
    - `query_internal_log_level_counts()`:
            A function which aggregates per-level counts for the
            current filter set.
    - `query_log_sessions()`:
            A function which returns persisted log sessions with
            associated log counts.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import json
import sqlite3
import uuid
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
    start_time: str | None,
    end_time: str | None,
    include_level: bool,
) -> tuple[str, list[Any], str | None]:
    normalized_levels = _parse_level_filters(level)
    normalized_module = _normalize_filter(module)
    normalized_search = _normalize_filter(search)
    normalized_source = _normalize_filter(source)
    normalized_session_id = _normalize_filter(session_id)
    normalized_start_time = _normalize_filter(start_time)
    normalized_end_time = _normalize_filter(end_time)

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
    if normalized_start_time:
        filters.append('timestamp >= ?')
        params.append(normalized_start_time)
    if normalized_end_time:
        filters.append('timestamp <= ?')
        params.append(normalized_end_time)
    if normalized_search:
        filters.append('message LIKE ?')
        params.append(f'%{normalized_search}%')

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ''
    return where_clause, params, normalized_levels[0] if normalized_levels else None


def _configure_internal_logs_connection(conn: sqlite3.Connection, enable_wal: bool = False) -> None:
    '''
    Applies pragmas to an internal logs database connection.

    :param conn: (sqlite3.Connection) -
        Represents the SQLite connection to configure.
    :param enable_wal: (bool) -
        Represents whether to enable Write-Ahead Logging for this connection.

    :return: (None)
    '''
    if enable_wal:
        conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA busy_timeout=5000;')


def ensure_internal_logs_schema(db_path: str) -> None:
    '''
    Ensures internal logs and session tables/indexes exist.

    :param db_path: (String) -
        Represents the path to the SQLite database.

    :return: (None)
    '''

    with sqlite3.connect(db_path, timeout=5) as conn:
        _configure_internal_logs_connection(conn, enable_wal=True)
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
                trace_id TEXT,
                event_id TEXT
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
        try:
            conn.execute('ALTER TABLE internal_logs ADD COLUMN event_id TEXT')
        except Exception:
            pass
        conn.execute(
            "UPDATE internal_logs SET event_id = lower(hex(randomblob(16))) WHERE event_id IS NULL"
        )
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
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_timestamp_id ON internal_logs(timestamp DESC, id DESC)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_internal_logs_session_timestamp_id ON internal_logs(session_id, timestamp DESC, id DESC)'
        )
        conn.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_internal_logs_event_id ON internal_logs(event_id) WHERE event_id IS NOT NULL'
        )
        conn.commit()


def create_log_session(
    db_path: str,
    session_id: str,
    started_at: str,
    log_file: str,
    source: str = DEFAULT_SOURCE,
) -> None:
    '''
    Inserts a new log session record.

    :param db_path: (String) -
        Represents the path to the SQLite database.
    :param session_id: (String) -
        Represents a unique ID for the current logging session.
    :param started_at: (String) -
        Represents the UTC session start timestamp.
    :param log_file: (String) -
        Represents the session log file path.
    :param source: (Optional[String]) -
        Represents the source token for the session.

    :return: (None)
    '''

    with sqlite3.connect(db_path, timeout=5) as conn:
        _configure_internal_logs_connection(conn)
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


def _normalize_event_id(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError('event_id must be a string')

    normalized = value.strip()
    if not normalized:
        raise ValueError('event_id is required')

    try:
        return uuid.UUID(normalized).hex
    except ValueError as exc:
        raise ValueError('event_id must be a valid UUID') from exc


def normalize_log_payload(payload: dict[str, Any]) -> dict[str, Any]:
    '''
    Validates and normalises a single internal log payload item.

    :param payload: (Dictionary) -
        Represents a log object received by the internal ingest endpoint.

    :return: (Dictionary) -
        Normalised payload ready for persistence.
    '''

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
    event_id = _normalize_event_id(payload.get('event_id'))

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
        'metadata': metadata,
        'exception': exception_data,
        'session_id': session_id,
        'trace_id': trace_id,
        'event_id': event_id,
    }


def insert_internal_logs(db_path: str, logs: list[dict[str, Any]]) -> int:
    '''
    Inserts normalised internal log items into storage.

    :param db_path: (String) -
        Represents the path to the SQLite database.
    :param logs: (List[Dictionary]) -
        Represents normalised log items ready for insertion.

    :return: (Integer) -
        Number of rows inserted.
    '''

    if not logs:
        return 0

    with sqlite3.connect(db_path, timeout=5) as conn:
        _configure_internal_logs_connection(conn)
        before_changes = conn.total_changes
        conn.executemany(
            '''
            INSERT OR IGNORE INTO internal_logs (
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
                trace_id,
                event_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    item['event_id'],
                )
                for item in logs
            ],
        )
        inserted_count = conn.total_changes - before_changes
        conn.commit()

    return inserted_count


def _normalise_exception_projection(
    metadata: Any,
    exception: Any,
) -> dict[str, str | None]:
    '''
    Builds canonical exception fields from historic and current log shapes.

    :param metadata: (Any) -
        Represents the persisted structured metadata.
    :param exception: (Any) -
        Represents the persisted top-level exception envelope.

    :return: (Dictionary) -
        Canonical exception type, message and traceback fields.
    '''

    metadata_fields = metadata if isinstance(metadata, dict) else {}
    exception_fields = exception if isinstance(exception, dict) else {}

    def first_string(*values: Any) -> str | None:
        return next(
            (value for value in values if isinstance(value, str)),
            None,
        )

    return {
        'exception_type': first_string(
            metadata_fields.get('exception_type'),
            exception_fields.get('type'),
        ),
        'exception_message': first_string(
            metadata_fields.get('exception_message'),
            metadata_fields.get('exception'),
            exception_fields.get('message'),
        ),
        'exception_traceback': first_string(
            exception_fields.get('traceback'),
        ),
    }


def query_internal_logs(
    db_path: str,
    page: int,
    page_size: int,
    level: str | None,
    module: str | None,
    search: str | None,
    source: str | None,
    session_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    '''
    Queries internal logs with pagination and optional filters.

    :param db_path: (String) -
        Represents the path to the SQLite database.
    :param page: (Integer) -
        Represents the result page number.
    :param page_size: (Integer) -
        Represents the number of records to return per page.
    :param level: (Optional[String]) -
        Represents one or more comma-delimited level filters.
    :param module: (Optional[String]) -
        Represents an optional module filter.
    :param search: (Optional[String]) -
        Represents an optional message search term.
    :param source: (Optional[String]) -
        Represents an optional source filter.
    :param session_id: (Optional[String]) -
        Represents an optional session ID filter.
    :param start_time: (Optional[String]) -
        Represents an optional ISO timestamp lower bound.
    :param end_time: (Optional[String]) -
        Represents an optional ISO timestamp upper bound.

    :return: (Tuple[List[Dictionary], Integer]) -
        A tuple containing result items and total count.
    '''

    where_clause, params, _ = _build_internal_logs_filters(
        level=level,
        module=module,
        search=search,
        source=source,
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
        include_level=True,
    )

    count_sql = f'SELECT COUNT(*) FROM internal_logs {where_clause}'
    data_sql = (
        'SELECT id, timestamp, level, logger, module, function, line, message, source, metadata, exception, session_id, trace_id, event_id '
        f'FROM internal_logs {where_clause} '
        'ORDER BY timestamp DESC, id DESC '
        'LIMIT ? OFFSET ?'
    )

    offset = (page - 1) * page_size

    with sqlite3.connect(db_path, timeout=5) as conn:
        _configure_internal_logs_connection(conn)
        conn.row_factory = sqlite3.Row
        total = conn.execute(count_sql, params).fetchone()[0]
        rows = conn.execute(data_sql, [*params, page_size, offset]).fetchall()

    items = []
    for row in rows:
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        exception = (
            json.loads(row['exception'])
            if row['exception']
            else None
        )
        items.append({
            'id': row['id'],
            'timestamp': row['timestamp'],
            'level': row['level'],
            'logger': row['logger'],
            'module': row['module'],
            'function': row['function'],
            'line': row['line'],
            'message': row['message'],
            'source': row['source'],
            'metadata': metadata,
            'exception': exception,
            **_normalise_exception_projection(metadata, exception),
            'session_id': row['session_id'],
            'trace_id': row['trace_id'],
            'event_id': row['event_id'],
        })

    return items, total


def query_internal_log_level_counts(
    db_path: str,
    level: str | None,
    module: str | None,
    search: str | None,
    source: str | None,
    session_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, int]:
    '''
    Aggregates per-level counts for the current filter set.

    :param db_path: (String) -
        Represents the path to the SQLite database.
    :param level: (Optional[String]) -
        Represents one or more comma-delimited level filters.
    :param module: (Optional[String]) -
        Represents an optional module filter.
    :param search: (Optional[String]) -
        Represents an optional message search term.
    :param source: (Optional[String]) -
        Represents an optional source filter.
    :param session_id: (Optional[String]) -
        Represents an optional session ID filter.
    :param start_time: (Optional[String]) -
        Represents an optional ISO timestamp lower bound.
    :param end_time: (Optional[String]) -
        Represents an optional ISO timestamp upper bound.

    :return: (Dictionary) -
        A dictionary keyed by standard level names.
    '''

    where_clause, params, _ = _build_internal_logs_filters(
        level=level,
        module=module,
        search=search,
        source=source,
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
        include_level=True,
    )

    sql = (
        'SELECT level, COUNT(*) AS count '
        f'FROM internal_logs {where_clause} '
        'GROUP BY level'
    )

    counts: dict[str, int] = {level_key: 0 for level_key in LEVEL_COUNT_KEYS}

    with sqlite3.connect(db_path, timeout=5) as conn:
        _configure_internal_logs_connection(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()

    for row in rows:
        level_name = str(row['level']).upper()
        if level_name in counts:
            counts[level_name] = int(row['count'])

    return counts


def query_log_sessions(db_path: str) -> list[dict[str, Any]]:
    '''
    Returns persisted log sessions with associated log counts.

    :param db_path: (String) -
        Represents the path to the SQLite database.

    :return: (List[Dictionary]) -
        Session records ordered by start time descending.
    '''

    sql = (
        'SELECT ls.session_id, ls.started_at, ls.log_file, ls.source, '
        'COUNT(il.id) AS log_count '
        'FROM log_sessions ls '
        'LEFT JOIN internal_logs il ON il.session_id = ls.session_id '
        'GROUP BY ls.id '
        'ORDER BY ls.started_at DESC'
    )
    with sqlite3.connect(db_path, timeout=5) as conn:
        _configure_internal_logs_connection(conn)
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
