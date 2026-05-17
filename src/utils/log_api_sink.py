#! /usr/bin/env python3

import atexit
import json
import os
import queue
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

from loguru import logger

from .internal_logs import create_log_session, ensure_internal_logs_schema


class InternalAPILogPipeline:
    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        queue_size: int = 2000,
        flush_interval_seconds: float = 1.0,
        batch_size: int = 100,
        logs_db_path: str | None = None,
        logs_dir: str = 'logs',
    ) -> None:
        self.endpoint = f'http://{host}:{port}/internal/logs'
        self.token = token
        self.flush_interval_seconds = flush_interval_seconds
        self.batch_size = batch_size
        self.logs_db_path = logs_db_path
        self.logs_dir = logs_dir
        self.session_id: str | None = None
        self.queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._worker,
            name='runebot-log-api-worker',
            daemon=True,
        )
        self._sink_id: int | None = None
        self._file_sink_id: int | None = None
        self._counters_lock = threading.Lock()
        self._total_enqueued = 0
        self._total_dropped = 0
        self._total_posted_successfully = 0
        self._total_post_failures = 0
        self._pending_retry: list[dict[str, Any]] | None = None

    def start(self) -> None:
        self._thread.start()
        self._sink_id = logger.add(self._sink, catch=True)
        if self.logs_db_path:
            self._start_session()

    def _start_session(self) -> None:
        started_at_dt = datetime.now(timezone.utc)
        started_at = started_at_dt.isoformat()
        session_id = uuid.uuid4().hex
        log_filename = started_at_dt.strftime('%Y-%m-%d_%H-%M-%S') + '.log'
        log_file = str(Path(self.logs_dir) / log_filename)
        os.makedirs(self.logs_dir, exist_ok=True)
        ensure_internal_logs_schema(self.logs_db_path)
        create_log_session(
            db_path=self.logs_db_path,
            session_id=session_id,
            started_at=started_at,
            log_file=log_file,
        )
        self.session_id = session_id
        self._file_sink_id = logger.add(log_file, catch=True)

    def stop(self) -> None:
        self._stop_event.set()
        if self._sink_id is not None:
            logger.remove(self._sink_id)
            self._sink_id = None
        if self._file_sink_id is not None:
            logger.remove(self._file_sink_id)
            self._file_sink_id = None
        if self._thread.is_alive():
            self._thread.join(timeout=max(2.0, self.flush_interval_seconds + 2.0))

    def get_stats(self) -> dict[str, int]:
        with self._counters_lock:
            return {
                'total_enqueued': self._total_enqueued,
                'total_dropped': self._total_dropped,
                'total_posted_successfully': self._total_posted_successfully,
                'total_post_failures': self._total_post_failures,
                'queue_size': self.queue.qsize(),
            }

    def _increment_counter(self, field_name: str, amount: int = 1) -> None:
        with self._counters_lock:
            setattr(self, field_name, getattr(self, field_name) + amount)

    def _make_json_safe(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {
                str(k): self._make_json_safe(v)
                for k, v in value.items()
            }
        if isinstance(value, (list, tuple, set)):
            return [self._make_json_safe(v) for v in value]
        return str(value)

    def _build_payload(self, record: dict[str, Any]) -> dict[str, Any]:
        timestamp = record['time'].astimezone(timezone.utc).isoformat()
        event_id = uuid.uuid4().hex
        exception = None
        record_exception = record.get('exception')
        if record_exception is not None:
            traceback_text = None
            if record_exception.type and record_exception.value and record_exception.traceback:
                traceback_text = ''.join(
                    traceback.format_exception(
                        record_exception.type,
                        record_exception.value,
                        record_exception.traceback,
                    )
                )
            exception = {
                'type': getattr(record_exception.type, '__name__', None) if record_exception.type else None,
                'message': str(record_exception.value) if record_exception.value else None,
                'traceback': traceback_text,
            }

        extra = record.get('extra') or {}
        trace_id = None
        if isinstance(extra, dict):
            trace_id = extra.get('trace_id')

        metadata = dict(extra) if isinstance(extra, dict) else {}
        metadata.pop('trace_id', None)

        return {
            'timestamp': timestamp,
            'level': record['level'].name,
            'logger': record.get('name'),
            'module': record.get('module'),
            'function': record.get('function'),
            'line': record.get('line'),
            'message': record['message'],
            'source': 'bot',
            'metadata': self._make_json_safe(metadata),
            'exception': exception,
            'session_id': self.session_id,
            'trace_id': trace_id,
            'event_id': event_id,
        }

    def _sink(self, message: Any) -> None:
        payload = self._build_payload(message.record)
        try:
            self.queue.put_nowait(payload)
            self._increment_counter('_total_enqueued')
        except queue.Full:
            self._increment_counter('_total_dropped')
            return

    def _post_batch(self, logs: list[dict[str, Any]]) -> bool:
        body = json.dumps({'logs': logs}).encode('utf-8')
        req = request.Request(
            self.endpoint,
            data=body,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}',
            },
        )

        try:
            with request.urlopen(req, timeout=2) as response:
                is_success = 200 <= response.status < 300
                if is_success:
                    self._increment_counter('_total_posted_successfully', len(logs))
                else:
                    self._increment_counter('_total_post_failures', len(logs))
                return is_success
        except Exception:
            self._increment_counter('_total_post_failures', len(logs))
            return False

    def _collect_batch(self) -> list[dict[str, Any]]:
        batch: list[dict[str, Any]] = []
        while len(batch) < self.batch_size:
            try:
                batch.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return batch

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            if self._pending_retry:
                if self._post_batch(self._pending_retry):
                    self._pending_retry = None
                else:
                    time.sleep(self.flush_interval_seconds)
                    continue

            try:
                first_item = self.queue.get(timeout=self.flush_interval_seconds)
            except queue.Empty:
                continue

            batch = [first_item]
            batch.extend(self._collect_batch())
            if not self._post_batch(batch):
                self._pending_retry = batch

        self._flush_on_shutdown(timeout_seconds=2.0)

    def _flush_on_shutdown(self, timeout_seconds: float) -> None:
        deadline = time.monotonic() + timeout_seconds

        if self._pending_retry:
            self._post_batch(self._pending_retry)
            self._pending_retry = None

        while time.monotonic() < deadline:
            batch = self._collect_batch()
            if not batch:
                break
            self._post_batch(batch)


_pipeline: InternalAPILogPipeline | None = None


def start_log_api_pipeline(
    host: str,
    port: int,
    token: str,
    logs_db_path: str | None = None,
    logs_dir: str = 'logs',
) -> InternalAPILogPipeline | None:
    if not token:
        return None

    global _pipeline
    if _pipeline is not None:
        return _pipeline

    _pipeline = InternalAPILogPipeline(
        host=host,
        port=port,
        token=token,
        logs_db_path=logs_db_path,
        logs_dir=logs_dir,
    )
    _pipeline.start()
    atexit.register(_pipeline.stop)
    return _pipeline
