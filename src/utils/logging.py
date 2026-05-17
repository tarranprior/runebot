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


def serialize_params(params: List[LogParam]) -> List[dict]:
    return [param.to_dict() for param in params]


def format_log_token(value: str | None) -> str:
    return f'<{value}>' if value is not None else '<unknown>'


def serialize_param(param: LogParam | None) -> list[dict]:
    return serialize_params([param] if param is not None else [])


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
        return f' {subject_token}: {operation_token} complete.'

    if stage == 'runtime_failure':
        return f'{subject_token}: {operation_token} runtime failure.'

    if stage == 'retry':
        return f'{subject_token}: retry {operation_token}.'

    if stage == 'failure':
        return f'{subject_token}: {operation_token} failure.'

    return f'{subject_token}: {operation_token}.'
