#! /usr/bin/env python3

'''
This module contains the internal HTTP API server for Runebot runtime
stats and internal log ingestion and query.

Classes:
    - `InternalStatsAPIServer`:
            A class which manages startup, shutdown, and request handling
            for internal statistics and log pipeline routes.

Functions:
    - `get_process_memory_bytes()`:
            A function which returns process memory usage in bytes
            on a best-effort basis.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import asyncio
import json
import threading
import time
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from concurrent.futures import TimeoutError as FuturesTimeoutError
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from loguru import logger
from version import VERSION

from .internal_logs import (
    ensure_internal_logs_schema,
    insert_internal_logs,
    normalize_log_payload,
    query_internal_log_level_counts,
    query_internal_logs,
    query_log_sessions,
)
from .runtime_stats import build_community_stats_payload


MAX_LOGS_PAGE_SIZE = 500


def get_process_memory_bytes() -> int | None:
    '''
    Returns process memory usage in bytes on a best-effort basis.

    :return: (Optional[Integer]) -
        Current process RSS in bytes when available.
    '''

    try:
        import psutil
    except ImportError:
        psutil = None

    if psutil is not None:
        try:
            return int(psutil.Process().memory_info().rss)
        except Exception:
            pass
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        ru_maxrss = getattr(usage, 'ru_maxrss', None)
        if ru_maxrss is None:
            return None
        return int(ru_maxrss * 1024)
    except ImportError:
        return None
    except Exception:
        return None


class InternalStatsAPIServer:
    '''
    Internal API server wrapper for stats, ingest, and log query endpoints.

    This class manages startup, shutdown, and request handling for
    internal statistics and log pipeline routes.
    '''

    def __init__(
        self,
        bot,
        token: str,
        host: str = '127.0.0.1',
        port: int = 8080,
        logs_db_path: str = 'runebot-logs.db',
        log_pipeline=None,
    ) -> None:
        '''
        Initialises a new internal API server instance.

        :param self: -
            Represents this object.
        :param bot: -
            Represents the active bot instance.
        :param token: (String) -
            Represents the internal API bearer token.
        :param host: (Optional[String]) -
            Represents the bind host for the HTTP server.
        :param port: (Optional[Integer]) -
            Represents the bind port for the HTTP server.
        :param logs_db_path: (Optional[String]) -
            Represents the internal logs database path.
        :param log_pipeline: (Optional[Any]) -
            Represents the active log API pipeline instance.

        :return: (None)
        '''

        self.bot = bot
        self.token = token
        self.host = host
        self.port = port
        self.logs_db_path = logs_db_path
        self.log_pipeline = log_pipeline
        self._server = None
        self._thread = None

    async def _build_payload(self) -> dict:
        '''
        Builds the community stats payload from current runtime state.

        :param self: -
            Represents this object.

        :return: (Dictionary) -
            Community stats payload for API responses.
        '''

        started_at_utc = getattr(self.bot, 'runtime_started_at_utc', None)
        return build_community_stats_payload(self.bot, started_at_utc)

    def _make_handler(self):
        '''
        Builds and returns the internal HTTP request handler class.

        :param self: -
            Represents this object.

        :return: -
            A configured BaseHTTPRequestHandler subclass.
        '''

        outer = self

        class InternalStatsHandler(BaseHTTPRequestHandler):
            def _send_json(self, status_code: int, payload: dict, add_auth_challenge: bool = False) -> None:
                body = json.dumps(payload).encode('utf-8')
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                if add_auth_challenge:
                    self.send_header('WWW-Authenticate', 'Bearer')
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (ConnectionAbortedError, BrokenPipeError) as exc:
                    logger.bind(
                        action='write_response',
                        stage='disconnect',
                        operation='send_json',
                        path=self.path,
                        status_code=status_code,
                        exception_type=type(exc).__name__,
                    ).warning('Internal API client disconnected before JSON response could be written.')

            def _authorised(self) -> tuple[bool, HTTPStatus]:
                if not outer.token:
                    return False, HTTPStatus.SERVICE_UNAVAILABLE

                auth_header = self.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return False, HTTPStatus.UNAUTHORIZED

                provided_token = auth_header.replace('Bearer ', '', 1).strip()
                if provided_token != outer.token:
                    return False, HTTPStatus.FORBIDDEN

                return True, HTTPStatus.OK

            def _read_json_body(self) -> tuple[dict | list | None, HTTPStatus | None]:
                content_length_header = self.headers.get('Content-Length', '0')

                try:
                    content_length = int(content_length_header)
                except (TypeError, ValueError):
                    return None, HTTPStatus.BAD_REQUEST

                if content_length <= 0:
                    return None, HTTPStatus.BAD_REQUEST

                try:
                    raw_body = self.rfile.read(content_length)
                    return json.loads(raw_body.decode('utf-8')), None
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return None, HTTPStatus.BAD_REQUEST

            def _validate_runelite_event_payload(self, payload: dict) -> str | None:
                event_type = payload.get('event_type')
                if not isinstance(event_type, str) or not event_type.strip():
                    return 'event_type is required and must be a non-empty string'

                if 'source' in payload and payload['source'] is not None and not isinstance(payload['source'], str):
                    return 'source must be a string'

                if 'plugin_version' in payload and payload['plugin_version'] is not None and not isinstance(payload['plugin_version'], str):
                    return 'plugin_version must be a string'

                if 'timestamp' in payload:
                    timestamp = payload['timestamp']
                    if timestamp is not None and not isinstance(timestamp, (str, int, float)):
                        return 'timestamp must be a string or number'

                if 'player_name' in payload and payload['player_name'] is not None and not isinstance(payload['player_name'], str):
                    return 'player_name must be a string'

                if 'world' in payload:
                    world = payload['world']
                    if world is not None and (not isinstance(world, int) or isinstance(world, bool)):
                        return 'world must be an integer'

                if 'data' in payload:
                    data = payload['data']
                    if data is not None and not isinstance(data, dict):
                        return 'data must be a JSON object'

                return None

            def _build_runelite_log_summary(self, payload: dict) -> dict[str, int | str | None]:
                # RuneLite ingest is future-facing groundwork for v1.1.0;
                # logs here stay sanitised and avoid full payload dumps.
                payload_size_bytes = None
                try:
                    payload_size_bytes = len(
                        json.dumps(payload, ensure_ascii=True, separators=(',', ':')).encode('utf-8')
                    )
                except (TypeError, ValueError):
                    payload_size_bytes = None

                return {
                    'event_type': payload.get('event_type'),
                    'payload_keys_count': len(payload),
                    'payload_size_bytes': payload_size_bytes,
                    'world': payload.get('world'),
                }

            def _handle_community_stats_request(self, require_auth: bool) -> None:
                if require_auth:
                    is_authorised, status_code = self._authorised()
                    if not is_authorised:
                        error_message = (
                            'Internal API endpoint is disabled'
                            if status_code == HTTPStatus.SERVICE_UNAVAILABLE
                            else 'Missing or invalid bearer token'
                        )
                        return self._send_json(
                            status_code,
                            {'error': error_message},
                            add_auth_challenge=(status_code == HTTPStatus.UNAUTHORIZED)
                        )

                try:
                    future = asyncio.run_coroutine_threadsafe(
                        outer._build_payload(),
                        outer.bot.loop
                    )
                    payload = future.result(timeout=5)
                    return self._send_json(HTTPStatus.OK, payload)
                except FuturesTimeoutError:
                    future.cancel()
                    logger.bind(
                        action='build_response',
                        stage='timeout',
                        operation='community_stats',
                        path=self.path,
                        timeout_seconds=5,
                    ).error('Community stats API timed out while collecting runtime stats.')
                    return self._send_json(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {'error': 'Timed out collecting runtime stats'}
                    )
                except Exception as exc:
                    logger.bind(
                        action='build_response',
                        stage='runtime_failure',
                        operation='community_stats',
                        path=self.path,
                        exception_type=type(exc).__name__,
                    ).opt(exception=exc).error('Community stats API failed to collect runtime stats.')
                    return self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {'error': 'Internal server error'}
                    )

            def _handle_runelite_event_request(self) -> None:
                is_authorised, status_code = self._authorised()
                if not is_authorised:
                    error_message = (
                        'Internal API endpoint is disabled'
                        if status_code == HTTPStatus.SERVICE_UNAVAILABLE
                        else 'Missing or invalid bearer token'
                    )
                    return self._send_json(
                        status_code,
                        {'error': error_message},
                        add_auth_challenge=(status_code == HTTPStatus.UNAUTHORIZED)
                    )

                payload, error_status = self._read_json_body()
                if error_status is not None:
                    return self._send_json(
                        error_status,
                        {'error': 'Invalid JSON body'}
                    )

                if not isinstance(payload, dict):
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {'error': 'JSON body must be an object'}
                    )

                validation_error = self._validate_runelite_event_payload(payload)
                if validation_error is not None:
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {'error': validation_error}
                    )

                event_type = payload['event_type'].strip()
                summary = self._build_runelite_log_summary(payload)
                logger.info(
                    f'Received RuneLite event: '
                    f'event_type={event_type}, '
                    f'world={summary["world"] if summary["world"] is not None else "unknown"}, '
                    f'payload_keys_count={summary["payload_keys_count"]}, '
                    f'payload_size_bytes={summary["payload_size_bytes"] if summary["payload_size_bytes"] is not None else "unknown"}'
                )
                return self._send_json(HTTPStatus.OK, {'ok': True})

            def _extract_log_items(self, payload: dict) -> tuple[list[dict] | None, str | None]:
                if 'logs' in payload:
                    items = payload.get('logs')
                    if not isinstance(items, list):
                        return None, 'logs must be an array'
                    return items, None

                return [payload], None

            def _handle_internal_logs_ingest_request(self) -> None:
                is_authorised, status_code = self._authorised()
                if not is_authorised:
                    error_message = (
                        'Internal API endpoint is disabled'
                        if status_code == HTTPStatus.SERVICE_UNAVAILABLE
                        else 'Missing or invalid bearer token'
                    )
                    return self._send_json(
                        status_code,
                        {'error': error_message},
                        add_auth_challenge=(status_code == HTTPStatus.UNAUTHORIZED)
                    )

                payload, error_status = self._read_json_body()
                if error_status is not None:
                    return self._send_json(
                        error_status,
                        {'error': 'Invalid JSON body'}
                    )

                if not isinstance(payload, dict):
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {'error': 'JSON body must be an object'}
                    )

                raw_items, extract_error = self._extract_log_items(payload)
                if extract_error is not None:
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {'error': extract_error}
                    )

                try:
                    validated_logs = [normalize_log_payload(item) for item in raw_items or []]
                except ValueError as exc:
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {'error': str(exc)}
                    )

                try:
                    inserted = insert_internal_logs(outer.logs_db_path, validated_logs)
                except Exception as exc:
                    logger.bind(
                        action='persist',
                        stage='runtime_failure',
                        operation='internal_logs_ingest',
                        path=self.path,
                        batch_size=len(validated_logs),
                        exception_type=type(exc).__name__,
                    ).opt(exception=exc).error('Failed to persist internal logs.')
                    return self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {'error': 'Failed to persist logs'}
                    )
                return self._send_json(HTTPStatus.OK, {'ok': True, 'inserted': inserted})

            def _parse_positive_int(self, raw_value: str | None, fallback: int) -> int:
                if raw_value is None:
                    return fallback
                try:
                    parsed = int(raw_value)
                    return parsed if parsed > 0 else fallback
                except ValueError:
                    return fallback

            def _parse_iso8601_timestamp(self, raw_value: str | None, field_name: str) -> tuple[str | None, datetime | None]:
                if raw_value is None:
                    return None, None

                normalized = raw_value.strip()
                if not normalized:
                    raise ValueError(f'{field_name} must be a valid ISO-8601 timestamp')

                iso_candidate = normalized.replace('Z', '+00:00')
                try:
                    parsed = datetime.fromisoformat(iso_candidate)
                except ValueError as exc:
                    raise ValueError(f'{field_name} must be a valid ISO-8601 timestamp') from exc

                if parsed.tzinfo is None:
                    raise ValueError(f'{field_name} must include a timezone offset')

                normalized_utc = parsed.astimezone(timezone.utc)
                return normalized_utc.isoformat(), normalized_utc

            def _handle_logs_query_request(self) -> None:
                is_authorised, status_code = self._authorised()
                if not is_authorised:
                    error_message = (
                        'Internal API endpoint is disabled'
                        if status_code == HTTPStatus.SERVICE_UNAVAILABLE
                        else 'Missing or invalid bearer token'
                    )
                    return self._send_json(
                        status_code,
                        {'error': error_message},
                        add_auth_challenge=(status_code == HTTPStatus.UNAUTHORIZED)
                    )

                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)

                page = self._parse_positive_int(params.get('page', [None])[0], 1)
                page_size = self._parse_positive_int(params.get('page_size', [None])[0], 50)
                page_size = min(page_size, MAX_LOGS_PAGE_SIZE)

                level = params.get('level', [None])[0]
                module = params.get('module', [None])[0]
                search = params.get('search', [None])[0]
                source = params.get('source', [None])[0]
                session_id = params.get('session_id', [None])[0]
                start_time_raw = params.get('start_time', [None])[0]
                end_time_raw = params.get('end_time', [None])[0]

                try:
                    start_time_filter, start_time_dt = self._parse_iso8601_timestamp(start_time_raw, 'start_time')
                    end_time_filter, end_time_dt = self._parse_iso8601_timestamp(end_time_raw, 'end_time')
                except ValueError as exc:
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {'error': str(exc)}
                    )

                if start_time_dt is not None and end_time_dt is not None and start_time_dt > end_time_dt:
                    return self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {'error': 'start_time must be less than or equal to end_time'}
                    )

                request_started_at = time.perf_counter()

                try:
                    items, total = query_internal_logs(
                        db_path=outer.logs_db_path,
                        page=page,
                        page_size=page_size,
                        level=level,
                        module=module,
                        search=search,
                        source=source,
                        session_id=session_id,
                        start_time=start_time_filter,
                        end_time=end_time_filter,
                    )
                    level_counts = query_internal_log_level_counts(
                        db_path=outer.logs_db_path,
                        level=level,
                        module=module,
                        search=search,
                        source=source,
                        session_id=session_id,
                        start_time=start_time_filter,
                        end_time=end_time_filter,
                    )
                except Exception as exc:
                    logger.bind(
                        action='query',
                        stage='runtime_failure',
                        operation='internal_logs_query',
                        path=self.path,
                        page=page,
                        page_size=page_size,
                        level=level,
                        module=module,
                        source=source,
                        session_id=session_id,
                        has_search=bool(search),
                        has_start_time=bool(start_time_filter),
                        has_end_time=bool(end_time_filter),
                        exception_type=type(exc).__name__,
                    ).opt(exception=exc).error('Failed to query internal logs.')
                    return self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {'error': 'Failed to query logs'}
                    )

                duration_ms = int((time.perf_counter() - request_started_at) * 1000)
                memory_bytes = get_process_memory_bytes()

                return self._send_json(
                    HTTPStatus.OK,
                    {
                        'items': items,
                        'pagination': {
                            'page': page,
                            'page_size': page_size,
                            'total': total,
                        },
                        'level_counts': level_counts,
                        'meta': {
                            'memory_bytes': memory_bytes,
                            'duration_ms': duration_ms,
                            'version': VERSION,
                        },
                    }
                )

            def _handle_logs_health_request(self) -> None:
                is_authorised, status_code = self._authorised()
                if not is_authorised:
                    error_message = (
                        'Internal API endpoint is disabled'
                        if status_code == HTTPStatus.SERVICE_UNAVAILABLE
                        else 'Missing or invalid bearer token'
                    )
                    return self._send_json(
                        status_code,
                        {'error': error_message},
                        add_auth_challenge=(status_code == HTTPStatus.UNAUTHORIZED)
                    )

                if outer.log_pipeline is None:
                    return self._send_json(
                        HTTPStatus.OK,
                        {'ok': True, 'pipeline_enabled': False, 'stats': None}
                    )

                return self._send_json(
                    HTTPStatus.OK,
                    {
                        'ok': True,
                        'pipeline_enabled': True,
                        'stats': outer.log_pipeline.get_stats()
                    }
                )

            def _handle_log_sessions_request(self) -> None:
                is_authorised, status_code = self._authorised()
                if not is_authorised:
                    error_message = (
                        'Internal API endpoint is disabled'
                        if status_code == HTTPStatus.SERVICE_UNAVAILABLE
                        else 'Missing or invalid bearer token'
                    )
                    return self._send_json(
                        status_code,
                        {'error': error_message},
                        add_auth_challenge=(status_code == HTTPStatus.UNAUTHORIZED)
                    )

                try:
                    sessions = query_log_sessions(outer.logs_db_path)
                except Exception as exc:
                    logger.bind(
                        action='query',
                        stage='runtime_failure',
                        operation='log_sessions_query',
                        path=self.path,
                        exception_type=type(exc).__name__,
                    ).opt(exception=exc).error('Failed to query log sessions.')
                    return self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {'error': 'Failed to query sessions'}
                    )

                return self._send_json(HTTPStatus.OK, {'sessions': sessions})

            def do_GET(self):
                route_path = urlparse(self.path).path

                if route_path == '/api/internal/community-stats':
                    return self._handle_community_stats_request(require_auth=True)

                if route_path == '/community-stats':
                    return self._handle_community_stats_request(require_auth=False)

                if route_path == '/logs/sessions':
                    return self._handle_log_sessions_request()

                if route_path == '/logs':
                    return self._handle_logs_query_request()

                if route_path == '/internal/logs/health':
                    return self._handle_logs_health_request()

                return self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {'error': 'Not found'}
                )

            def do_POST(self):
                route_path = urlparse(self.path).path

                if route_path == '/internal/runelite/events':
                    return self._handle_runelite_event_request()

                if route_path == '/internal/logs':
                    return self._handle_internal_logs_ingest_request()

                return self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {'error': 'Not found'}
                )

            def log_message(self, format, *args):
                return

        return InternalStatsHandler

    def start(self) -> bool:
        '''
        Starts the threaded internal API server.

        :param self: -
            Represents this object.

        :return: (bool) -
            True when startup completes.
        '''

        ensure_internal_logs_schema(self.logs_db_path)
        handler = self._make_handler()
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="runebot-internal-api",
            daemon=True,
        )
        self._thread.start()

        base_url = f"http://{self.host}:{self.port}"
        protected = bool(self.token)

        endpoints = {
            "community_stats_public": {
                "path": "/community-stats",
                "url": f"{base_url}/community-stats",
                "auth": "public",
            }
        }

        if protected:
            endpoints.update({
                "community_stats_internal": {
                    "path": "/api/internal/community-stats",
                    "url": f"{base_url}/api/internal/community-stats",
                    "auth": "bearer",
                },
                "runelite_ingest": {
                    "path": "/internal/runelite/events",
                    "url": f"{base_url}/internal/runelite/events",
                    "auth": "bearer",
                },
                "log_ingest": {
                    "path": "/internal/logs",
                    "url": f"{base_url}/internal/logs",
                    "auth": "bearer",
                },
                "log_query": {
                    "path": "/logs",
                    "url": f"{base_url}/logs",
                    "auth": "bearer",
                },
                "log_sessions": {
                    "path": "/logs/sessions",
                    "url": f"{base_url}/logs/sessions",
                    "auth": "bearer",
                },
                "log_health": {
                    "path": "/internal/logs/health",
                    "url": f"{base_url}/internal/logs/health",
                    "auth": "bearer",
                },
            })

        logger.bind(
            host=self.host,
            port=self.port,
            protected_endpoints=protected,
            endpoints=endpoints,
        ).success("Internal API(s) are active.")

        if not protected:
            logger.warning(
                "RUNEBOT_INTERNAL_API_TOKEN not set. Internal API(s) with protection are inactive."
            )

        return True

    def stop(self) -> None:
        '''
        Stops and closes the internal API server if running.

        :param self: -
            Represents this object.

        :return: (None)
        '''

        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
