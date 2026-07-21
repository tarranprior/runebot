#! /usr/bin/env python3

'''
This module contains various common helper utilities to help RuneBot
function properly.

Functions:
    - `convert_date_to_duration()`:
            Converts unix timestamps to "human friendly" durations.
    - `configuration()`:
            Reads the configuration file (config.json) and returns its contents as a dictionary.
    - `extract_colour()`:
            Extracts the most frequent colour from an image with a given URL.
    - `normalize_price()`:
            Reformats (normalises) price integers into RuneScape currency.
    - `slugify()`:
            Replaces spaces with underscores in a search query for parsing purposes (URL formatting).
    - `build_loading_button_view()`:
            Builds a temporary view from the current message components and disables only the clicked button.

Each function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import asyncio
import sys
import os
import io
import json
from datetime import datetime, timezone

from typing import Callable, Mapping, Optional
from urllib.request import Request, urlopen
from humanfriendly import format_timespan
import disnake
from disnake import MessageInteraction
from colorthief import ColorThief as ColourThief


def convert_date_to_duration(date_1, date_2) -> str:
    '''
    Helper function which converts unix timestamps to "human friendly"
    durations. (https://github.com/xolox/python-humanfriendly)

    :param date_1: (Datetime) -
        Represents a datetime object. The first datetime object to compare.
    :param date_2: (Datetime) -
        Represents a datetime object. The second datetime object to compare.

    :return: (String) -
        A string indicating the duration between the two
        datetime objects in a "human-friendly" format.
    '''

    diff = date_1 - date_2
    seconds = diff.total_seconds()
    timespan = format_timespan(seconds).split(',')[0].split(' and ')[0]
    return f'{timespan} ago'


def configuration() -> dict:
    '''
    Helper function which reads the configuration file (config.json)
    and returns its contents as a dictionary.

    :return: (Dictionary) -
        A dictionary representing the contents of the configuration file.
    '''

    if os.path.isfile('config.json'):
        with open('config.json', encoding='utf-8') as json_file:
            data = json.load(json_file)
            return data
    else:
        sys.exit('Configuration file not found. Please add it and try again.')


def utc_now_iso() -> str:
    '''
    Helper function which returns the current UTC timestamp in ISO
    format.

    :return: (String) -
        The current UTC timestamp in ISO format.
    '''

    return datetime.now(timezone.utc).isoformat()


def _download_and_extract_colour(
    image_url: str,
    headers: tuple[tuple[str, str], ...],
    *,
    timeout: float = 60,
) -> tuple[int, int, int]:
    '''
    Helper function which synchronously downloads an image and extracts its
    most frequent colour using color-thief-py.

    This function contains only the blocking network and image-processing work
    so it can be executed outside the Discord event loop.

    :param image_url: (String) -
        Represents the URL of the image.
    :param headers: (Tuple) -
        Represents immutable HTTP request headers for the web request.
    :param timeout: (Float) -
        Represents the maximum number of seconds for the image request.

    :return: (Tuple) -
        A tuple representing the dominant RGB colour value of the image.
    '''

    request_image = Request(image_url, headers=dict(headers))
    open_image = urlopen(request_image, timeout=timeout)
    image_data = io.BytesIO(open_image.read())
    colour_thief = ColourThief(image_data)
    return colour_thief.get_color(quality=1)


async def extract_colour(
    self,
    guild_id: int,
    guild_owner_id: int,
    image_url: str,
    headers: Mapping[str, str],
    on_failure: Callable[[Exception], None] | None = None,
) -> tuple[int, int, int]:
    '''
    Helper function which extracts the most frequent colour from an image with
    a given URL, using color-thief-py.
    (https://github.com/fengsp/color-thief-py)

    :param self: -
        Represents this object.
    :param guild_id: (Integer) -
        Represents the guild id.
    :param guild_owner_id: (Integer) -
        Represents the id of the guild owner.
    :param image_url: (String) -
        Represents the URL/to/image.
    :param headers: (Dictionary) -
        Represents HTTP request headers for the web request.
    :param on_failure: (Optional[Callable]) -
        Receives a handled colour-extraction exception before the fallback
        colour is returned.

    :return: (Tuple) -
        A tuple representing the dominant RGB colour value of the image,
        or the default blurple colour if extraction is disabled or fails.
    '''

    from .database import get_colour_mode

    if image_url:
        colour_mode = await get_colour_mode(self, guild_id, guild_owner_id)
        if colour_mode:
            try:
                dominant_colour = await asyncio.to_thread(
                    _download_and_extract_colour,
                    image_url,
                    tuple(headers.items()),
                    timeout=60,
                )
                return (dominant_colour)
            except Exception as exc:
                if on_failure is not None:
                    try:
                        on_failure(exc)
                    except Exception:
                        pass
    return ((
        disnake.Colour.og_blurple().r,
        disnake.Colour.og_blurple().g,
        disnake.Colour.og_blurple().b
    ))


def normalize_price(price: int) -> Optional[str]:
    '''
    Helper function which reformats (normalises) price integers into
    RuneScape currency (eg. 550000 to 550K gp)

    :param price: (Integer) -
        Represents a price integer.

    :return: (String or None) -
        The normalised price value in a formatted string,
        or None if price is negative.
    '''

    if price < 1000:
        normalized_price = f'{price:,.0f} gp'
    elif price < 1000000:
        normalized_price = f'{price / 1000:,.1f} K gp'
    elif price < 1000000000:
        normalized_price = f'{price / 1000000:,.1f} M gp'
    else:
        return f'{price / 1000000000:,.2f} B gp'

    return normalized_price


def slugify(search_query: str) -> str:
    '''
    Helper function which replaces spaces (' ' characters) with underscores
    in a search query for parsing purposes (URL formatting.)

    :param search_query: (String) -
        Represents a search value.
    
    :return: (String) -
        The new "slugified" search query with underscores.
    '''

    search_query = search_query.replace(' ', '_')
    return search_query


def get_component_custom_id_metadata(
    custom_id: str | None
) -> tuple[str | None, str | None]:
    '''
    Safely extracts component metadata from a custom_id value.

    :param custom_id: (String[Optional]) -
        Represents a component custom_id.

    :return: (Tuple[String[Optional], String[Optional]]) -
        The component prefix and action, or None values when unavailable.
    '''

    if not isinstance(custom_id, str) or not custom_id:
        return None, None

    prefix_parts = custom_id.split(':', 1)
    component_prefix = prefix_parts[0] or None
    component_action = None

    if len(prefix_parts) > 1 and prefix_parts[1]:
        payload = prefix_parts[1]
        separator_indexes = [
            idx
            for idx in (payload.find(':'), payload.find(','))
            if idx != -1
        ]
        split_index = min(separator_indexes) if separator_indexes else -1
        component_action = payload[:split_index] if split_index != -1 else payload
        if component_action == '':
            component_action = None

    return component_prefix, component_action


async def ack_wrong_component_user(
    inter,
    bound_logger,
    command: str,
    *,
    operation: str = 'wrong_component_user',
    invocation_source: str | None = None,
    trace_id: str | None = None,
    origin_trace_id: str | None = None,
    started_at: float | None = None,
    emit_runtime_failure: bool = True,
) -> None:
    '''
    Sends a neutral ephemeral acknowledgement when a component is used
    by someone other than the original author.

    :param inter: (MessageInteraction) -
        Represents the component interaction.
    :param bound_logger: (BoundCommandLogger) -
        Represents the command logger used for structured warning logs.
    :param command: (String) -
        Represents the command name used in log output.
    :param operation: (String) -
        Represents the component failure operation.
    :param invocation_source: (String[Optional]) -
        Represents the source of the interaction.

    :return: (None)
    '''
    await ack_component_failure(
        inter,
        bound_logger,
        command,
        description='Only the original author can use these buttons.',
        title='Nothing interesting happens.',
        operation=operation,
        invocation_source=invocation_source,
        trace_id=trace_id,
        origin_trace_id=origin_trace_id,
        started_at=started_at,
        emit_runtime_failure=emit_runtime_failure,
    )


async def ack_component_failure(
    inter,
    bound_logger,
    command: str,
    *,
    description: str,
    title: str = 'Nothing interesting happens.',
    operation: str = 'component_failure',
    invocation_source: str | None = None,
    trace_id: str | None = None,
    origin_trace_id: str | None = None,
    started_at: float | None = None,
    emit_runtime_failure: bool = True,
) -> None:
    '''
    Sends a neutral ephemeral acknowledgement for a handled component
    failure.

    :param inter: (MessageInteraction) -
        Represents the component interaction.
    :param bound_logger: (BoundCommandLogger) -
        Represents the command logger used for structured warning logs.
    :param command: (String) -
        Represents the command name used in log output.
    :param description: (String) -
        Represents the embed description shown to the user.
    :param title: (String) -
        Represents the embed title shown to the user.
    :param operation: (String) -
        Represents the component failure operation.
    :param invocation_source: (String[Optional]) -
        Represents the source of the interaction.

    :return: (None)
    '''
    from disnake import MessageInteraction

    custom_id = getattr(getattr(inter, 'component', None), 'custom_id', None)
    component_prefix, component_action = get_component_custom_id_metadata(custom_id)

    from utils.logging import build_log_message, elapsed_ms

    computed_invocation_source = (
        'component_callback' if isinstance(inter, MessageInteraction) else 'slash_command'
    )
    invocation = invocation_source or computed_invocation_source

    try:
        from utils.embeds import EmbedFactory
        from version import DISPLAY_VERSION
        from config import SUPPORT_SERVER

        embed, view = EmbedFactory().create(
            title=title,
            description=description,
            thumbnail_url=None,
            colour=0x8B8B8B,
            button_label='Support Server',
            button_url=SUPPORT_SERVER,
        )
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

        if inter.response.is_done():
            await inter.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await inter.response.send_message(embed=embed, view=view, ephemeral=True)
    except Exception as exc:
        if emit_runtime_failure:
            bound_logger.error(
                inter,
                build_log_message(
                    command=command,
                    stage='runtime_failure',
                    operation=operation,
                ),
                exc=exc,
                invocation_source=invocation,
                action='fail',
                stage='runtime_failure',
                operation=operation,
                trace_id=trace_id,
                component_type='component',
                handled=False,
                expected_failure=False,
                user_visible=False,
                component_prefix=component_prefix,
                component_action=component_action,
                **(
                    {'origin_trace_id': origin_trace_id}
                    if origin_trace_id is not None
                    else {}
                ),
                **(
                    {'duration_ms': elapsed_ms(started_at)}
                    if started_at is not None
                    else {}
                ),
            )
        raise

    bound_logger.warning(
        inter,
        build_log_message(
            command=command,
            stage='failure',
            operation=operation,
        ),
        invocation_source=invocation,
        action='fail',
        stage='failure',
        operation=operation,
        trace_id=trace_id,
        component_type='component',
        handled=True,
        expected_failure=True,
        user_visible=True,
        component_prefix=component_prefix,
        component_action=component_action,
        **(
            {'origin_trace_id': origin_trace_id}
            if origin_trace_id is not None
            else {}
        ),
        **(
            {'duration_ms': elapsed_ms(started_at)}
            if started_at is not None
            else {}
        ),
    )


async def ack_runtime_failure(
    inter,
    *,
    description: str = 'Something went wrong while handling that request. Please try again.',
    title: str = 'Nothing interesting happens.',
    raise_on_failure: bool = False,
) -> None:
    '''
    Sends a neutral ephemeral acknowledgement for a generic runtime
    failure without emitting additional logs.

    :param inter: (Interaction) -
        Represents the interaction to acknowledge.
    :param description: (String) -
        Represents the embed description shown to the user.
    :param title: (String) -
        Represents the embed title shown to the user.
    :return: (None)
    '''
    try:
        from utils.embeds import EmbedFactory
        from version import DISPLAY_VERSION
        from config import SUPPORT_SERVER

        embed, view = EmbedFactory().create(
            title=title,
            description=description,
            thumbnail_url=None,
            colour=0x8B8B8B,
            button_label='Support Server',
            button_url=SUPPORT_SERVER,
        )
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

        if inter.response.is_done():
            await inter.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await inter.response.send_message(embed=embed, view=view, ephemeral=True)
    except Exception:
        if raise_on_failure:
            raise
        return


def is_invalid_username(
    username: str | None,
    max_chars: int,
    blacklist_chars: list[str],
) -> bool:
    '''
    Returns whether a username violates OSRS length or character rules.

    :param username: (String[Optional]) -
        Represents a username value.
    :param max_chars: (Integer) -
        Represents the maximum allowed username length.
    :param blacklist_chars: (List[String]) -
        Represents disallowed username characters.

    :return: (Boolean) -
        True when the username is invalid, otherwise False.
    '''

    if username is None:
        return False

    if len(username) > max_chars:
        return True

    return any(char in username for char in blacklist_chars)


def is_discord_mention(value: str | None) -> bool:
    '''
    Returns True when the provided value is a Discord user mention.

    :param value: (String[Optional]) -
        Represents the value to test for Discord mention shape.
    :return: (Boolean) -
        True when the value looks like a Discord mention, otherwise False.
    '''

    if value is None:
        return False

    if not isinstance(value, str):
        return False

    return value.startswith('<@') and value.endswith('>')


def get_discord_mention_id(value: str) -> str:
    '''
    Extracts the numeric user ID from a Discord mention string.

    :param value: (String) -
        Represents the mention string to extract from.
    :return: (String) -
        Represents the numeric ID.
    '''

    if value.startswith('<@!'):
        return value[3:-1]
    if value.startswith('<@'):
        return value[2:-1]
    return value


def build_loading_button_view(inter: MessageInteraction) -> disnake.ui.View:
    '''
    Builds a temporary view from message components and disables only
    the clicked button.

    :param inter: (MessageInteraction) -
        Represents a message component interaction triggered by a button.

    :return: (disnake.ui.View) -
        A temporary view with only the clicked button disabled.
    '''

    view = disnake.ui.View(timeout=None)

    clicked_custom_id = getattr(inter.component, 'custom_id', None)
    clicked_url = getattr(inter.component, 'url', None)

    for row_index, row in enumerate(inter.message.components):
        for component in row.children:
            if component.type != disnake.ComponentType.button:
                continue

            is_clicked = (
                (clicked_custom_id and component.custom_id == clicked_custom_id)
                or
                (clicked_url and component.url == clicked_url)
            )

            button = disnake.ui.Button(
                label=component.label,
                style=component.style,
                custom_id=component.custom_id,
                url=component.url,
                emoji=component.emoji,
                disabled=component.disabled or is_clicked,
                row=row_index
            )
            view.add_item(button)

    return view
