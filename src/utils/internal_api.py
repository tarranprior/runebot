#! /usr/bin/env python3

import asyncio
import json
import threading

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


            def _authorised(self):
                auth_header = self.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return False, HTTPStatus.UNAUTHORIZED

                provided_token = auth_header.replace('Bearer ', '', 1).strip()
                if provided_token != outer.token:
                    return False, HTTPStatus.FORBIDDEN

                return True, HTTPStatus.OK


            def do_GET(self):
                if self.path != '/api/internal/community-stats':
                    return self._send_json(
                        HTTPStatus.NOT_FOUND,
                        {'error': 'Not found'}
                    )

                is_authorised, status_code = self._authorised()
                if not is_authorised:
                    error_message = 'Missing or invalid bearer token'
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
                    logger.error('Internal stats API timed out while collecting runtime stats.')
                    return self._send_json(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {'error': 'Timed out collecting runtime stats'}
                    )
                except Exception as exc:
                    logger.error(f'Internal stats API failed to collect runtime stats: {exc}')
                    return self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {'error': 'Internal server error'}
                    )


            def log_message(self, format, *args):
                return

        return InternalStatsHandler


    def start(self) -> bool:
        if not self.token:
            logger.warning(
                'Internal stats API disabled: RUNEBOT_INTERNAL_API_TOKEN is not set.'
            )
            return False

        handler = self._make_handler()
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name='runebot-internal-api',
            daemon=True
        )
        self._thread.start()

        logger.success(
            f'Internal stats API enabled at http://{self.host}:{self.port}/api/internal/community-stats'
        )
        return True


    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
