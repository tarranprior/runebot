#! /usr/bin/env python3

'''
This module contains logging helper utilities for Runebot command
and internal execution logs.

Classes:
    - `LogParam`:
            A dataclass which represents a single structured log parameter
            used in command and internal log payloads.
    - `BoundCommandLogger`:
            A class which wraps a bind function and provides convenience
            methods for emitting command log events at each log level.

Functions:
    - `build_interaction_log_context()`:
            A function which builds normalised interaction metadata for
            structured command logs.
    - `build_command_log_bind()`:
            A function which builds a structured bind payload for
            command-facing logs.
    - `emit_command_log()`:
            A function which emits a command log event at the provided level.
    - `emit_bound_command_log()`:
            A function which resolves bind payload via a bind function
            and emits a command log.
    - `emit_internal_log()`:
            A function which emits an internal (non-command) structured
            log event.
    - `build_log_message()`:
            A function which builds a canonical human-readable log message
            from structured logging context.
    - `build_internal_log_message()`:
            A function which builds an internal execution log message.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List
from loguru import logger

@dataclass
class LogParam:
    kind: str
    label: str
    value: Any
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _snowflake_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def build_interaction_log_context(inter: Any) -> dict:
    '''
    Builds normalised interaction metadata for structured command logs.

    :param inter: (Any) -
        Represents a slash-command interaction or component interaction object.

    :return: (Dictionary) -
        A dictionary containing normalised user, guild, channel,
        and interaction type fields.
    '''

    user = getattr(inter, 'author', None) or getattr(inter, 'user', None)
    interaction_type = getattr(inter, 'type', None)
    return {
        'user_id': _snowflake_str(getattr(user, 'id', None)),
        'user_name': getattr(user, 'name', None),
        'user_display_name': getattr(user, 'display_name', None),
        'guild_id': _snowflake_str(getattr(inter, 'guild_id', None)),
        'channel_id': _snowflake_str(getattr(inter, 'channel_id', None)),
        'interaction_type': str(interaction_type) if interaction_type is not None else None,
    }


def build_command_log_bind(
    *,
    command: str,
    inter: Any,
    action: str,
    stage: str,
    operation: str = 'search',
    invocation_source: str = 'slash_command',
    invocation_mode: str | None = None,
    search_query: str | None = None,
    resolved_search_term: str | None = None,
    resolved_page_title: str | None = None,
    resolution_source: str | None = None,
    trace_id: str | None = None,
    log_params: list | None = None,
    **extra,
) -> dict:
    '''
    Builds a structured bind payload for command-facing logs.

    :param command: (String) -
        Represents the command name (without slash prefix).
    :param inter: (Any) -
        Represents a slash-command interaction or component interaction object.
    :param action: (String) -
        Represents the action token for the log event.
    :param stage: (String) -
        Represents the execution stage token.
    :param operation: (Optional[String]) -
        Represents the operation name. Defaults to 'search'.
    :param invocation_source: (Optional[String]) -
        Represents the invocation source (slash command, component etc.).
    :param invocation_mode: (Optional[String]) -
        Represents the invocation mode context, if available.
    :param search_query: (Optional[String]) -
        Represents the original user query.
    :param resolved_search_term: (Optional[String]) -
        Represents the resolved search term.
    :param resolved_page_title: (Optional[String]) -
        Represents the resolved page title.
    :param resolution_source: (Optional[String]) -
        Represents the resolution source metadata.
    :param trace_id: (Optional[String]) -
        Represents the trace ID for correlation.
    :param log_params: (Optional[List]) -
        Represents structured log params for rendering/query.
    :param extra: -
        Represents additional bind fields to include.

    :return: (Dictionary) -
        A filtered payload containing only non-None values.
    '''

    payload = {
        'command': command,
        'trace_id': trace_id,
        'invocation_source': invocation_source,
        'action': action,
        'stage': stage,
        'operation': operation,
        'invocation_mode': invocation_mode,
        'search_query': search_query,
        'resolved_search_term': resolved_search_term,
        'resolved_page_title': resolved_page_title,
        'resolution_source': resolution_source,
        'log_params': log_params,
        **build_interaction_log_context(inter),
        **extra,
    }
    return {k: v for k, v in payload.items() if v is not None}


def emit_command_log(
    *,
    level: str,
    bind_payload: dict,
    message: str,
    exc: Exception | None = None,
) -> None:
    '''
    Emits a command log event at the provided level.

    :param level: (String) -
        Represents the log level to emit (debug/info/success/warning/error).
    :param bind_payload: (Dictionary) -
        Represents structured metadata fields bound to the logger.
    :param message: (String) -
        Represents the final human-readable log message.
    :param exc: (Optional[Exception]) -
        Represents an exception to attach when emitting an error log.

    :return: (None)
    '''

    bound_logger = logger.bind(**bind_payload)

    if level == 'error':
        bound_logger.opt(exception=exc).error(message)
        return

    if level == 'debug':
        bound_logger.debug(message)
        return

    if level == 'info':
        bound_logger.info(message)
        return

    if level == 'warning':
        bound_logger.warning(message)
        return

    if level == 'success':
        bound_logger.success(message)
        return

    raise ValueError(f'Unsupported log level: {level}')


def emit_bound_command_log(
    bind_func,
    inter,
    level: str,
    message: str,
    exc: Exception | None = None,
    **bind_kwargs,
) -> None:
    '''
    Resolves bind payload via a bind function and emits a command log.

    :param bind_func: -
        Represents a callable that builds bind payload from interaction context.
    :param inter: -
        Represents an interaction object used by the bind function.
    :param level: (String) -
        Represents the log level to emit.
    :param message: (String) -
        Represents the log message to emit.
    :param exc: (Optional[Exception]) -
        Represents an exception for error logs.
    :param bind_kwargs: -
        Represents keyword arguments forwarded to the bind function.

    :return: (None)
    '''

    bind_payload = bind_func(inter, **bind_kwargs)
    emit_command_log(
        level=level,
        bind_payload=bind_payload,
        message=message,
        exc=exc,
    )


class BoundCommandLogger:
    '''
    Convenience wrapper for emitting command logs using a shared bind function.

    The provided bind function is reused across all helper methods to
    keep command logging payloads consistent.
    '''

    def __init__(self, bind_func) -> None:
        '''
        Initialises a bound command logger.

        :param bind_func: -
            Represents a callable that builds a bind payload from
            interaction context and bind keyword arguments.

        :return: (None)
        '''

        self._bind_func = bind_func

    def debug(self, inter, message: str, **bind_kwargs) -> None:
        emit_bound_command_log(
            self._bind_func,
            inter,
            level='debug',
            message=message,
            **bind_kwargs,
        )

    def info(self, inter, message: str, **bind_kwargs) -> None:
        emit_bound_command_log(
            self._bind_func,
            inter,
            level='info',
            message=message,
            **bind_kwargs,
        )

    def success(self, inter, message: str, **bind_kwargs) -> None:
        emit_bound_command_log(
            self._bind_func,
            inter,
            level='success',
            message=message,
            **bind_kwargs,
        )

    def warning(self, inter, message: str, **bind_kwargs) -> None:
        emit_bound_command_log(
            self._bind_func,
            inter,
            level='warning',
            message=message,
            **bind_kwargs,
        )

    def error(self, inter, message: str, exc: Exception, **bind_kwargs) -> None:
        emit_bound_command_log(
            self._bind_func,
            inter,
            level='error',
            message=message,
            exc=exc,
            **bind_kwargs,
        )


def serialize_params(params: List[LogParam]) -> List[dict]:
    return [param.to_dict() for param in params]


def format_log_token(value: str | None) -> str:
    return f'<{value}>' if value is not None else '<unknown>'


def serialize_param(param: LogParam | None) -> list[dict]:
    return serialize_params([param] if param is not None else [])


def build_search_query_log_params(
    search_query: str,
) -> list[dict]:
    return [
        {'kind': 'query', 'label': 'search_query', 'value': search_query},
    ]


def build_resolved_search_log_params(
    *,
    search_query: str,
    resolved_search_term: str,
    resolved_page_title: str,
) -> list[dict]:
    return [
        {'kind': 'query', 'label': 'search_query', 'value': search_query},
        {'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term},
        {'kind': 'page_title', 'label': 'resolved_page_title', 'value': resolved_page_title},
    ]


def build_expected_user_visible_failure_metadata(exc: Exception) -> dict:
    return {
        'handled': True,
        'expected_failure': True,
        'user_visible': True,
        'exception_type': type(exc).__name__,
        'exception': str(exc),
    }


def build_unexpected_user_visible_failure_metadata() -> dict:
    return {
        'handled': True,
        'expected_failure': False,
        'user_visible': True,
    }


def serialize_resolved_username(
    resolved_username: str | None,
    *,
    account_type: str = None,
    resolution_source: str | None = None,
) -> list[dict]:
    if not resolved_username:
        return []

    return serialize_param(
        build_resolved_username_param(
            resolved_username,
            account_type=account_type,
            resolution_source=resolution_source,
        )
    )


def build_resolved_username_param(
    resolved_username: str,
    account_type: str | None = None,
    resolution_source: str | None = None,
) -> LogParam:
    '''
    Returns a LogParam for the semantic token 'resolved_username'.
    Optionally includes account_type and resolution_source in details.
    '''
    details = {}
    if account_type is not None:
        details["account_type"] = account_type
    if resolution_source is not None:
        details["resolution_source"] = resolution_source
    return LogParam(
        kind="resolved_username",
        label="resolved_username",
        value=resolved_username,
        details=details,
    )


def build_stats_resolution_params(
    *,
    original_username: str | None,
    resolved_username: str,
    resolution_source: str,
    default_account_id: int | None = None,
    account_type: str | None = None,
) -> list[LogParam]:
    '''
    Returns an ordered list of LogParam for stats resolution events.
    '''
    params = []
    if resolution_source == "default_account" and default_account_id is not None:
        details = {"resolved_username": resolved_username}
        if account_type is not None:
            details["account_type"] = account_type
        params.append(LogParam(
            kind="default_account",
            label="default_account",
            value=default_account_id,
            details=details,
        ))
    else:
        details = {"resolution_source": resolution_source}
        params.append(LogParam(
            kind="username",
            label="username",
            value=original_username or resolved_username,
            details=details,
        ))
    params.append(build_resolved_username_param(
        resolved_username,
        account_type=account_type,
        resolution_source=resolution_source,
    ))
    return params


def build_stats_failure_params(
    *,
    original_username: str | None,
    resolved_username: str | None,
    resolution_source: str,
    default_account_id: int | None = None,
    account_type: str | None = None,
) -> list[LogParam]:
    '''
    Returns an ordered list of LogParam for stats failure events.
    '''
    params = []
    if original_username:
        params.append(LogParam(kind="username", label="username", value=original_username))
    if resolution_source == "default_account" and default_account_id is not None:
        params.append(LogParam(kind="default_account", label="default_account", value=default_account_id))
    if resolved_username:
        params.append(build_resolved_username_param(
            resolved_username,
            account_type=account_type,
            resolution_source=resolution_source,
        ))
    return params


def build_log_message(
    *,
    command: str,
    stage: str,
    operation: str | None = None,
    subject: str | None = None,
    resolved: str | None = None,
    include_user: bool = True,
) -> str:
    '''
    Builds a canonical human-readable log message from structured logging
    context. Tokens are wrapped in angle brackets for UI rendering.
    '''
    command_token = f'/{command}'
    user_prefix = f'Request from {format_log_token("user")} for ' if include_user else 'Request for '

    if stage == 'resolve':
        if resolved is not None:
            return (
                f'{user_prefix}{command_token}: '
                f'resolve {format_log_token(subject)} to "{resolved}".'
            )
        return (
            f'{user_prefix}{command_token}: '
            f'resolve {format_log_token(subject)}.'
        )

    if stage == 'start':
        if subject is not None:
            return (
                f'{user_prefix}{command_token}: '
                f'start {format_log_token(operation)} for {format_log_token(subject)}.'
            )
        return (
            f'{user_prefix}{command_token}: '
            f'start {format_log_token(operation)}.'
        )

    if stage == 'complete':
        if subject is not None:
            return (
                f'{user_prefix}{command_token}: '
                f'{format_log_token(operation)} complete for {format_log_token(subject)}.'
            )
        return (
            f'{user_prefix}{command_token}: '
            f'{format_log_token(operation)} complete.'
        )

    if stage == 'runtime_failure':
        return (
            f'{user_prefix}{command_token}: '
            f'{format_log_token(operation)} runtime failure.'
        )

    if stage == 'failure':
        return (
            f'{user_prefix}{command_token}: '
            f'{format_log_token(operation)} failure.'
        )

    return f'{user_prefix}{command_token}.'


def build_internal_log_message(
    *,
    stage: str,
    operation: str | None = None,
    subject: str | None = None,
    resolved: str | None = None,
) -> str:
    '''
    Builds an internal execution log message.
    Keep this separate from slash-command UI request logs.
    '''
    subject_token = format_log_token(subject) if subject is not None else '<unknown>'
    operation_token = format_log_token(operation) if operation is not None else '<unknown>'

    if stage == 'resolve':
        if resolved is not None:
            return f'{subject_token}: resolve {operation_token} to "{resolved}".'
        return f'{subject_token}: resolve {operation_token}.'

    if stage == 'start':
        return f'{subject_token}: start {operation_token}.'

    if stage == 'complete':
        return f'{subject_token}: {operation_token} complete.'

    if stage == 'runtime_failure':
        return f'{subject_token}: {operation_token} runtime failure.'

    if stage == 'retry':
        return f'{subject_token}: retry {operation_token}.'

    if stage == 'failure':
        return f'{subject_token}: {operation_token} failure.'

    return f'{subject_token}: {operation_token}.'


def emit_internal_log(
    *,
    level: str,
    stage: str,
    operation: str,
    subject: str | None = None,
    resolved: str | None = None,
    trace_id: str | None = None,
    log_params: list | None = None,
    **extra,
) -> None:
    '''
    Emits an internal (non-command) structured log event.

    :param level: (String) -
        Represents the log level to emit.
    :param stage: (String) -
        Represents the execution stage token.
    :param operation: (String) -
        Represents the operation name for the event.
    :param subject: (Optional[String]) -
        Represents the subject token for the event.
    :param resolved: (Optional[String]) -
        Represents resolved output used by resolve-stage events.
    :param trace_id: (Optional[String]) -
        Represents the trace ID for correlation.
    :param log_params: (Optional[List]) -
        Represents structured log parameters for rendering/query.
    :param extra: -
        Represents additional metadata fields to bind to the event.

    :return: (None)
    '''

    message = build_internal_log_message(
        stage=stage,
        operation=operation,
        subject=subject,
        resolved=resolved,
    )

    payload = {
        'trace_id': trace_id,
        'action': operation,
        'stage': stage,
        'operation': operation,
        'subject': subject,
        'resolved': resolved,
        'log_params': log_params,
        **extra,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    bound_logger = logger.bind(**payload)

    log_method = getattr(bound_logger, level, bound_logger.debug)
    log_method(message)
