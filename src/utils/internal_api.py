#! /usr/bin/env python3

import asyncio
import json
import threading
from urllib.parse import urlparse

from concurrent.futures import TimeoutError as FuturesTimeoutError
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from loguru import logger

from .runtime_stats import build_community_stats_payload


class InternalStatsAPIServer:
    def __init__(self, bot, token: str, host: str = '127.0.0.1', port: int = 8080) -> None:
        self.bot = bot
        self.token = token
        self.host = host
        self.port = port
        self._server = None
        self._thread = None

    async def _build_payload(self) -> dict:
        started_at_utc = getattr(self.bot, 'runtime_started_at_utc', None)
        return build_community_stats_payload(self.bot, started_at_utc)

    def _make_handler(self):
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
                self.wfile.write(body)

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

            def _safe_payload_preview(self, payload: dict, max_length: int = 1000) -> str:
                preview = json.dumps(payload, ensure_ascii=True, separators=(',', ':'))
                if len(preview) > max_length:
                    return f'{preview[:max_length]}...'
                return preview

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
                    logger.error('Community stats API timed out while collecting runtime stats.')
                    return self._send_json(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {'error': 'Timed out collecting runtime stats'}
                    )
                except Exception as exc:
                    logger.error(f'Community stats API failed to collect runtime stats: {exc}')
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
                player_name = payload.get('player_name')
                world = payload.get('world')
                safe_payload = self._safe_payload_preview(payload)
                logger.info(
                    f'Received RuneLite event: '
                    f'event_type={event_type}, '
                    f'player_name={player_name or "unknown"}, '
                    f'world={world if world is not None else "unknown"}, '
                    f'payload={safe_payload}'
                )
                return self._send_json(HTTPStatus.OK, {'ok': True})

            def do_GET(self):
                route_path = urlparse(self.path).path

                if route_path == '/api/internal/community-stats':
                    return self._handle_community_stats_request(require_auth=True)

                if route_path == '/community-stats':
                    return self._handle_community_stats_request(require_auth=False)

                return self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {'error': 'Not found'}
                )

            def do_POST(self):
                route_path = urlparse(self.path).path

                if route_path == '/internal/runelite/events':
                    return self._handle_runelite_event_request()

                return self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {'error': 'Not found'}
                )

            def log_message(self, format, *args):
                return

        return InternalStatsHandler

    def start(self) -> bool:
        handler = self._make_handler()
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name='runebot-internal-api',
            daemon=True
        )
        self._thread.start()

        if self.token:
            logger.success(
                f'Community stats API enabled at '
                f'http://{self.host}:{self.port}/community-stats '
                f'(public via reverse proxy) and '
                f'http://{self.host}:{self.port}/api/internal/community-stats '
                f'(bearer auth required). '
                f'RuneLite ingest available at '
                f'http://{self.host}:{self.port}/internal/runelite/events '
                f'(bearer auth required)'
            )
        else:
            logger.warning(
                f'Community stats API enabled at '
                f'http://{self.host}:{self.port}/community-stats, but '
                f'/api/internal/community-stats and /internal/runelite/events are disabled because '
                f'RUNEBOT_INTERNAL_API_TOKEN is not set.'
            )

        return True

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
