#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `wikipedia`
command, allowing users to search for general article information from
the official Old School RuneScape wikipedia.

Classes:
    - `Wikipedia`:
            A class for handling the `wikipedia` command.
    - `Dropdown`:
            A class for creating dropdown options that can be added
            to a `DropdownView` instance.
    - `DropdownView`:
            A view class for creating dropdowns in the response.

Key Functions:
    - `search_wikipedia(...)`, `wikipedia(...)`, and
      `search_query_autocomplete(...)`:
            Functions for searching for and retrieving Wikipedia articles,
            as well as creating a slash command and autocomplete query for
            the `wikipedia` command.
    - `callback(self, inter: MessageInteraction)`:
            A callback function for dropdown selection.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `wikipedia` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import disnake
import time
import uuid

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, MessageInteraction, Option, OptionType
from loguru import logger

import exceptions
from config import *
from templates.bot import Bot
from utils import *
from utils.logging import (
    BoundCommandLogger,
    build_command_log_bind,
    build_interaction_log_context,
    build_log_message,
    log_colour_extraction_failure,
    elapsed_ms,
)


class Wikipedia(commands.Cog, name='wikipedia'):
    '''
    A class which represents the Wikipedia cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Wikipedia class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot
        self._wiki_log = BoundCommandLogger(self._wiki_bind)


    @staticmethod
    def _invocation_source(
        inter: ApplicationCommandInteraction | MessageInteraction
    ) -> str:
        return (
            'component_callback'
            if isinstance(inter, MessageInteraction)
            else 'slash_command'
        )


    def _wiki_bind(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        *,
        action: str,
        stage: str,
        operation: str = 'search',
        invocation_mode: str | None = None,
        search_query: str | None = None,
        resolved_search_term: str | None = None,
        resolved_page_title: str | None = None,
        resolution_source: str | None = None,
        trace_id: str | None = None,
        log_params: list | None = None,
        **extra,
    ) -> dict:
        return build_command_log_bind(
            command='wikipedia',
            inter=inter,
            action=action,
            stage=stage,
            operation=operation,
            invocation_source=self._invocation_source(inter),
            trace_id=trace_id,
            log_params=log_params,
            invocation_mode=invocation_mode,
            search_query=search_query,
            resolved_search_term=resolved_search_term,
            resolved_page_title=resolved_page_title,
            resolution_source=resolution_source,
            **extra,
        )

    async def search_wikipedia(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        search_query: str,
        trace_id: str | None = None,
        invocation_mode_override: str | None = None,
        started_at: float | None = None,
        emit_expected_failure: bool = True,
    ) -> Tuple[disnake.Embed, disnake.ui.View, str, str]:
        '''
        Primary function for the `wikipedia` command which takes a search
        query and returns corresponding data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction | MessageInteraction) -
            Represents an interaction with an application command or component callback.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, disnake.ui.View, str, str] -
            An embed, view, resolved search term, and resolved page title.
        '''

        invocation_mode = (
            invocation_mode_override
            if invocation_mode_override is not None
            else ('feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit')
        )
        original_query = search_query
        resolved_search_term = FEELING_LUCKY if invocation_mode == 'feeling_lucky' else search_query
        resolution_source = 'wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query'

        try:
            page_content = parse_page(BASE_URL, resolved_search_term, HEADERS, trace_id=trace_id)
            attributes = parse_all(page_content)
            title = attributes['title']
            resolved_search_term = title
            description = attributes['description']
            infobox = attributes['infobox']
            options = attributes['options']
            thumbnail_url = attributes['thumbnail_url']

            self._wiki_log.info(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='resolve',
                    operation='search',
                    subject='search_query',
                    resolved=title,
                ),
                action='resolve',
                stage='resolve',
                trace_id=trace_id,
                search_query=original_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=title,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=[
                    {
                        'kind': 'query',
                        'label': 'search_query',
                        'value': original_query,
                    },
                    {
                        'kind': 'query',
                        'label': 'resolved_search_term',
                        'value': resolved_search_term,
                    },
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': title,
                    },
                    {
                        'kind': 'resolver_input',
                        'label': 'resolver_input',
                        'value': FEELING_LUCKY if invocation_mode == 'feeling_lucky' else resolved_search_term,
                    },
                ],
            )

            normalized_query = search_query.rstrip('/')
            if 'Money making guide/' in normalized_query:
                button_url = f'{BASE_URL}Money_making_guide/{slugify(title)}'
            else:
                button_url = f'{BASE_URL}{slugify(title)}'

            colour = disnake.Colour.from_rgb(
                *await extract_colour(
                    self,
                    inter.guild_id,
                    inter.guild.owner_id,
                    thumbnail_url,
                    HEADERS,
                    on_failure=lambda exc: log_colour_extraction_failure(
                        self._wiki_log,
                        inter,
                        'wikipedia',
                        thumbnail_url,
                        exc,
                        trace_id=trace_id,
                        log_params=[
                            {'kind': 'query', 'label': 'search_query', 'value': original_query},
                            {'kind': 'page_title', 'label': 'resolved_page_title', 'value': title},
                        ],
                        search_query=original_query,
                        resolved_search_term=resolved_search_term,
                        resolved_page_title=title,
                        resolution_source=resolution_source,
                        invocation_mode=invocation_mode,
                    ),
                )
            )

            if description:
                embed, view = EmbedFactory().create(
                    title=title,
                    description=description.pop(),
                    colour=colour, infobox=infobox,
                    thumbnail_url=thumbnail_url,
                    button_url=button_url
                )
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                embed.timestamp = inter.created_at

                if len(embed.description) < 84:
                    embed.set_footer(
                        text=(f'To view more information about this page, click the button below.\nRunebot {DISPLAY_VERSION}')
                    )
                return embed, view, resolved_search_term, title

            self._wiki_log.debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='start',
                    operation='disambiguation',
                    subject='dropdown',
                ),
                action='start',
                stage='start',
                operation='disambiguation',
                trace_id=trace_id,
                search_query=original_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=title,
                invocation_mode=invocation_mode,
                log_params=[
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': title,
                    },
                    {
                        'kind': 'options_count',
                        'label': 'options_count',
                        'value': len(options) if options is not None else 0,
                    },
                ],
            )

            embed = EmbedFactory().create(
                title=title,
                description=(
                    f'{title} may refer to several articles. Use the dropdown below to select an option.'
                )
            )
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
            embed.timestamp = inter.created_at

            view = DropdownView(options, self, trace_id=trace_id)
            return embed, view, resolved_search_term, title

        except (exceptions.Nonexistence, exceptions.StubArticle, exceptions.WikiRequestFailed) as exc:
            if emit_expected_failure:
                self._wiki_log.warning(
                    inter,
                    build_log_message(
                        command='wikipedia',
                        stage='failure',
                        operation='search',
                    ),
                    action='fail',
                    stage='failure',
                    trace_id=trace_id,
                    search_query=original_query,
                    resolved_search_term=resolved_search_term,
                    resolution_source=resolution_source,
                    invocation_mode=invocation_mode,
                    log_params=[
                        {
                            'kind': 'query',
                            'label': 'search_query',
                            'value': original_query,
                        },
                        {
                            'kind': 'query',
                            'label': 'resolved_search_term',
                            'value': resolved_search_term,
                        },
                    ],
                    exception_type=type(exc).__name__,
                    exception=str(exc),
                    handled=True,
                    expected_failure=True,
                    user_visible=True,
                    **({'duration_ms': elapsed_ms(started_at)} if started_at is not None else {}),
                )
            raise
        except Exception:
            raise


    @commands.slash_command(
        name='wikipedia',
        description='Search for an article from the official OldSchool RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for an article. Start typing for suggestions or hit `I\'m feeling lucky` for a random page!',
                type=OptionType.string,
                required=True
            ),
        ],
    )
    async def wikipedia(
        self,
        inter: disnake.ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the `search_wikipedia` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolved_search_term = FEELING_LUCKY if invocation_mode == 'feeling_lucky' else search_query
        trace_id = uuid.uuid4().hex
        started_at = time.perf_counter()

        self._wiki_log.info(
            inter,
            build_log_message(
                command='wikipedia',
                stage='start',
                operation='search',
            ),
            action='start',
            stage='start',
            operation='search',
            search_query=search_query,
            invocation_mode=invocation_mode,
            resolution_source='wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query',
            trace_id=trace_id,
            log_params=[
                {
                    'kind': 'query',
                    'label': 'search_query',
                    'value': search_query,
                }
            ],
        )

        try:
            await inter.response.defer()
            embed, view, resolved_search_term, resolved_page_title = await self.search_wikipedia(
                inter,
                search_query,
                trace_id=trace_id,
                started_at=started_at,
            )
            if isinstance(view, DropdownView):
                view.attach_interaction_context(inter, invocation_mode=invocation_mode)
                message = await inter.followup.send(embed=embed, view=view, wait=True)
                view.message = message
            else:
                await inter.followup.send(embed=embed, view=view)

            self._wiki_log.success(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='complete',
                    operation='search',
                ),
                action='complete',
                stage='complete',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=resolved_page_title,
                invocation_mode=invocation_mode,
                resolution_source='wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query',
                duration_ms=elapsed_ms(started_at),
                log_params=[
                    {
                        'kind': 'query',
                        'label': 'search_query',
                        'value': search_query,
                    },
                    {
                        'kind': 'query',
                        'label': 'resolved_search_term',
                        'value': resolved_search_term,
                    },
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': resolved_page_title,
                    },
                ],
            )

        except (exceptions.Nonexistence, exceptions.StubArticle, exceptions.WikiRequestFailed) as exc:
            expected_description = str(exc)

            if isinstance(exc, exceptions.StubArticle):
                title = 'This project page is a stub.'
                thumbnail_url = THUMBNAILS['stub']
                colour = 0x60533E
            elif isinstance(exc, exceptions.WikiRequestFailed):
                title = 'Nothing interesting happens.'
                thumbnail_url = None
                colour = 0xB72615
            else:
                title = 'Nothing interesting happens.'
                thumbnail_url = None
                colour = 0x8B8B8B

            embed, view = EmbedFactory().create(
                title=title,
                description=expected_description,
                thumbnail_url=thumbnail_url,
                colour=colour,
                button_label='Support Server',
                button_url=SUPPORT_SERVER
            )
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

            if inter.response.is_done():
                await inter.followup.send(embed=embed, view=view)
            else:
                await inter.response.send_message(embed=embed, view=view)
            return

        except Exception as exc:
            self._wiki_log.error(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='runtime_failure',
                    operation='search',
                ),
                exc=exc,
                action='fail',
                stage='runtime_failure',
                operation='search',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                invocation_mode=invocation_mode,
                resolution_source='wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query',
                handled=True,
                expected_failure=False,
                user_visible=True,
                duration_ms=elapsed_ms(started_at),
            )

            await ack_runtime_failure(inter)
            return


    @wikipedia.autocomplete('search_query')
    async def search_query_autocomplete(self, search_query: str) -> (Union[List[str], str]):
        '''
        Creates a selection of autocomplete suggestions once the user begins
        typing.

        :param self: -
            Represents this object.
        :param search_query: (String) -
            Represents a search query.

        :return: (Union[List[String], String]) -
            A list of possible autocomplete suggestions,
            or "I'm feeling lucky".
        '''

        autocomplete_suggestions = await get_wikipedia_suggestions(self)

        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


class Dropdown(disnake.ui.StringSelect):
    '''
    A class which contains logic for the dropdown options (Select Menu)
    that can be added to a `DropdownView` instance.
    '''

    def __init__(self, options: list, cog, trace_id: str | None = None) -> None:
        '''
        Initialises a new instance of the Dropdown class.

        :param options: (List) -
            A list of dropdown options.
        :param cog: -
            The Wikipedia cog instance.
        
        :return: (None)
        '''

        self.bot = Bot
        self._cog = cog
        self.trace_id = trace_id

        super().__init__(
            placeholder='Select an option...',
            min_values=1,
            max_values=1,
            options=options,
        )


    async def callback(self, inter: MessageInteraction):
        '''
        The callback function for dropdown selection (Select Menu.)

        :param self: -
            Represents this object.
        :param inter: (MessageInteraction) -
            Represents a message component interaction triggered by the dropdown.

        :return: (None)
        '''

        trace_id = uuid.uuid4().hex
        origin_trace_id = self.trace_id
        selected_value = self.values[0] if self.values else None
        started_at = time.perf_counter()

        self._cog._wiki_log.info(
            inter,
            build_log_message(
                command='wikipedia',
                stage='start',
                operation='search',
            ),
            action='start',
            stage='start',
            operation='search',
            trace_id=trace_id,
            origin_trace_id=origin_trace_id,
            invocation_mode='dropdown_selection',
            search_query=selected_value,
            component_type='dropdown',
            selected_value=selected_value,
            log_params=[
                {
                    'kind': 'query',
                    'label': 'search_query',
                    'value': selected_value,
                }
            ],
        )

        try:
            self._cog._wiki_log.debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='start',
                    operation='defer',
                    subject='dropdown',
                ),
                action='defer',
                stage='start',
                operation='defer',
                trace_id=trace_id,
                origin_trace_id=origin_trace_id,
                invocation_mode='dropdown_selection',
                component_type='dropdown',
                selected_value=selected_value,
            )
            await inter.response.defer()

            embed, view, resolved_search_term, resolved_page_title = await self._cog.search_wikipedia(
                inter,
                selected_value,
                trace_id=trace_id,
                invocation_mode_override='dropdown_selection',
                started_at=started_at,
                emit_expected_failure=False,
            )

            self._cog._wiki_log.debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='start',
                    operation='followup_send',
                    subject='dropdown',
                ),
                action='start',
                stage='start',
                operation='followup_send',
                trace_id=trace_id,
                origin_trace_id=origin_trace_id,
                invocation_mode='dropdown_selection',
                component_type='dropdown',
                selected_value=selected_value,
            )

            if isinstance(view, DropdownView):
                view.attach_interaction_context(inter, invocation_mode='dropdown_selection')
                message = await inter.followup.send(embed=embed, view=view, wait=True)
                view.message = message
            else:
                await inter.followup.send(embed=embed, view=view)

            self._cog._wiki_log.debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='complete',
                    operation='followup_send',
                    subject='dropdown',
                ),
                action='complete',
                stage='complete',
                operation='followup_send',
                trace_id=trace_id,
                origin_trace_id=origin_trace_id,
                invocation_mode='dropdown_selection',
                component_type='dropdown',
                selected_value=selected_value,
            )

            self._cog._wiki_log.success(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='complete',
                    operation='search',
                ),
                action='complete',
                stage='complete',
                operation='search',
                invocation_mode='dropdown_selection',
                trace_id=trace_id,
                origin_trace_id=origin_trace_id,
                search_query=selected_value,
                resolved_search_term=resolved_search_term,
                resolved_page_title=resolved_page_title,
                resolution_source='user_query',
                component_type='dropdown',
                selected_value=selected_value,
                log_params=[
                    {
                        'kind': 'query',
                        'label': 'search_query',
                        'value': selected_value,
                    },
                    {
                        'kind': 'query',
                        'label': 'resolved_search_term',
                        'value': resolved_search_term,
                    },
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': resolved_page_title,
                    },
                ],
                duration_ms=elapsed_ms(started_at),
            )
        except (exceptions.Nonexistence, exceptions.StubArticle, exceptions.WikiRequestFailed) as exc:
            try:
                if isinstance(exc, exceptions.StubArticle):
                    title = 'This project page is a stub.'
                    thumbnail_url = THUMBNAILS['stub']
                    colour = 0x60533E
                elif isinstance(exc, exceptions.WikiRequestFailed):
                    title = 'Nothing interesting happens.'
                    thumbnail_url = None
                    colour = 0xB72615
                else:
                    title = 'Nothing interesting happens.'
                    thumbnail_url = None
                    colour = 0x8B8B8B

                embed, view = EmbedFactory().create(
                    title=title,
                    description=str(exc),
                    thumbnail_url=thumbnail_url,
                    colour=colour,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

                is_public_dropdown_result = isinstance(exc, exceptions.StubArticle)

                if inter.response.is_done():
                    await inter.followup.send(
                        embed=embed,
                        view=view,
                        ephemeral=not is_public_dropdown_result,
                    )
                else:
                    await inter.response.send_message(
                        embed=embed,
                        view=view,
                        ephemeral=not is_public_dropdown_result,
                    )
            except Exception as fallback_exc:
                self._cog._wiki_log.error(
                    inter,
                    build_log_message(
                        command='wikipedia',
                        stage='runtime_failure',
                        operation='search',
                    ),
                    exc=exc,
                    action='fail',
                    stage='runtime_failure',
                    operation='search',
                    invocation_mode='dropdown_selection',
                    search_query=selected_value,
                    component_type='dropdown',
                    selected_value=selected_value,
                    trace_id=trace_id,
                    origin_trace_id=origin_trace_id,
                    handled=False,
                    expected_failure=False,
                    user_visible=False,
                    fallback_exception_type=type(fallback_exc).__name__,
                    fallback_exception=str(fallback_exc),
                    duration_ms=elapsed_ms(started_at),
                )
                raise exc from fallback_exc

            self._cog._wiki_log.warning(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
                operation='search',
                invocation_mode='dropdown_selection',
                search_query=selected_value,
                component_type='dropdown',
                selected_value=selected_value,
                trace_id=trace_id,
                origin_trace_id=origin_trace_id,
                handled=True,
                expected_failure=True,
                user_visible=True,
                exception_type=type(exc).__name__,
                exception=str(exc),
                duration_ms=elapsed_ms(started_at),
            )
            return

        except Exception as exc:
            fallback_exc = None
            try:
                if inter.response.is_done():
                    await inter.followup.send(
                        'Something went wrong while handling that selection.',
                        ephemeral=True,
                    )
                else:
                    await inter.response.send_message(
                        'Something went wrong while handling that selection.',
                        ephemeral=True,
                    )
            except Exception as response_exc:
                fallback_exc = response_exc

            fallback_succeeded = fallback_exc is None
            self._cog._wiki_log.error(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='runtime_failure',
                    operation='search',
                ),
                exc=exc,
                action='fail',
                stage='runtime_failure',
                operation='search',
                invocation_mode='dropdown_selection',
                search_query=selected_value,
                component_type='dropdown',
                selected_value=selected_value,
                trace_id=trace_id,
                origin_trace_id=origin_trace_id,
                handled=fallback_succeeded,
                expected_failure=False,
                user_visible=fallback_succeeded,
                **(
                    {
                        'fallback_exception_type': type(fallback_exc).__name__,
                        'fallback_exception': str(fallback_exc),
                    }
                    if fallback_exc is not None
                    else {}
                ),
                duration_ms=elapsed_ms(started_at),
            )
            if fallback_exc is not None:
                raise exc from fallback_exc
            return


class DropdownView(disnake.ui.View):
    '''
    A view class for creating dropdowns in the response.
    '''

    TIMEOUT_SECONDS = 180

    def __init__(self, options: list, cog, trace_id: str | None = None) -> None:
        '''
        Initialises a new instance of the DropdownView class.

        :param options: (List) -
            A list of options for the dropdown.
        :param cog: -
            The Wikipedia cog instance.

        :return: (None)
        '''
        self.bot = Bot
        self._cog = cog
        self.trace_id = trace_id
        self.message: disnake.Message | None = None
        self.request_context: dict[str, str] = {}
        super().__init__(timeout=self.TIMEOUT_SECONDS)
        self.add_item(Dropdown(options, cog, trace_id=trace_id))

    def attach_interaction_context(
        self,
        inter: disnake.ApplicationCommandInteraction | MessageInteraction,
        *,
        invocation_mode: str | None = None,
    ) -> None:
        raw_context: dict[str, str | None] = {
            **build_interaction_log_context(inter),
            'invocation_source': self._cog._invocation_source(inter),
            'invocation_mode': invocation_mode,
        }
        
        if raw_context.get('interaction_type') == 'None':
            raw_context['interaction_type'] = None

        context_payload: dict[str, str | None] = {
            'user_id': raw_context.get('user_id'),
            'user_name': raw_context.get('user_name'),
            'user_display_name': raw_context.get('user_display_name'),
            'guild_id': raw_context.get('guild_id'),
            'channel_id': raw_context.get('channel_id'),
            'interaction_type': raw_context.get('interaction_type'),
            'invocation_source': raw_context.get('invocation_source'),
            'invocation_mode': raw_context.get('invocation_mode'),
        }
        self.request_context = {k: v for k, v in context_payload.items() if v is not None}

    def _log_lifecycle_event(
        self,
        *,
        inter: MessageInteraction | None,
        event: str,
        trace_id: str | None,
        stage: str,
        has_message_ref: bool,
        level: str,
        exc: Exception | None = None,
    ) -> None:
        log_params = [
            {
                'kind': 'component',
                'label': 'component_type',
                'value': 'dropdown',
            },
            {
                'kind': 'reason',
                'label': 'reason',
                'value': event,
            },
        ]

        payload = {
            'command': 'wikipedia',
            'action': 'deactivate',
            'stage': stage,
            'operation': 'disambiguation',
            'component_type': 'dropdown',
            'reason': event,
            'trace_id': trace_id,
            'has_message_ref': has_message_ref,
            'log_params': log_params,
        }

        if inter is None and self.request_context:
            payload.update(self.request_context)

        include_user = inter is not None or bool(self.request_context.get('user_id') or self.request_context.get('user_name'))

        message = build_log_message(
            command='wikipedia',
            stage=stage,
            operation='disambiguation',
            subject='dropdown' if stage == 'complete' else None,
            include_user=include_user,
        )

        if stage == 'runtime_failure':
            payload['cleanup_failed'] = True
            if exc is not None:
                payload['exception_type'] = type(exc).__name__
                payload['exception'] = str(exc)

        if inter is not None:
            helper_kwargs = dict(payload)
            if 'invocation_mode' not in helper_kwargs:
                helper_kwargs['invocation_mode'] = 'dropdown_selection'
            if level == 'info':
                self._cog._wiki_log.info(inter, message, **helper_kwargs)
            else:
                self._cog._wiki_log.debug(inter, message, **helper_kwargs)
            return

        bound_logger = logger.bind(**payload)
        if stage == 'runtime_failure' and exc is not None:
            bound_logger = bound_logger.opt(exception=exc)

        if level == 'info':
            bound_logger.info(message)
        else:
            bound_logger.debug(message)

    async def deactivate(
        self,
        *,
        inter: MessageInteraction | None = None,
        event: str,
        trace_id: str | None = None,
    ) -> None:
        effective_trace_id = trace_id or self.trace_id

        for item in self.children:
            item.disabled = True

        if self.message is None:
            self._log_lifecycle_event(
                inter=inter,
                event=event,
                trace_id=effective_trace_id,
                stage='complete',
                has_message_ref=False,
                level='debug',
            )
            return

        try:
            await self.message.edit(view=self)
            self._log_lifecycle_event(
                inter=inter,
                event=event,
                trace_id=effective_trace_id,
                stage='complete',
                has_message_ref=True,
                level='info',
            )
        except Exception as exc:
            self._log_lifecycle_event(
                inter=inter,
                event=event,
                trace_id=effective_trace_id,
                stage='runtime_failure',
                has_message_ref=True,
                level='debug',
                exc=exc,
            )

    async def on_timeout(self) -> None:
        await self.deactivate(event='timeout', trace_id=self.trace_id)


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `wikipedia` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Wikipedia(bot))
