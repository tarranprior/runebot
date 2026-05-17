#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `quests`
command, allowing users to search for quest information from the official
Old School RuneScape wikipedia.

Classes:
    - `Quests`: A class for handling the `quest` command.

Key Functions:
    - `quests(...)` and `search_query_autocomplete(...)`:
            Functions for creating a slash command and autocomplete query,
            respectively.
    - `search_quests(...)`:
            A function for searching the Old School RuneScape wiki for quest
            information on a specified query.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `quests` command.

Exceptions:
    - `NoQuestData`:
            Raised when there is no quest data available for a given query.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import random
import uuid

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType
from utils.logging import (
    build_command_log_bind,
    build_expected_user_visible_failure_metadata,
    build_log_message,
    build_resolved_search_log_params,
    build_search_query_log_params,
    build_unexpected_user_visible_failure_metadata,
    emit_command_log,
)

import exceptions
from config import *
from templates.bot import Bot
from utils import *


class Quests(commands.Cog, name='quests'):
    '''
    A class which represents the Quests cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Quests class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot


    @staticmethod
    def _invocation_source(
        inter: ApplicationCommandInteraction
    ) -> str:
        return 'slash_command'


    def _quests_bind(
        self,
        inter: ApplicationCommandInteraction,
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
            command='quests',
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


    def _log_quests_debug(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='debug',
            bind_payload=self._quests_bind(inter, **bind_kwargs),
            message=message,
        )
    

    def _log_quests_info(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='info',
            bind_payload=self._quests_bind(inter, **bind_kwargs),
            message=message,
        )


    def _log_quests_success(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='success',
            bind_payload=self._quests_bind(inter, **bind_kwargs),
            message=message,
        )


    def _log_quests_error(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        exc: Exception,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='error',
            bind_payload=self._quests_bind(inter, **bind_kwargs),
            message=message,
            exc=exc,
        )


    def _log_quests_warning(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='warning',
            bind_payload=self._quests_bind(inter, **bind_kwargs),
            message=message,
        )


    async def search_quest(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str,
        trace_id: str | None = None,
    ) -> Tuple[disnake.Embed, disnake.ui.View, str, str]:
        '''
        Primary function for the `quests` command which takes a search
        query and returns corresponding quest data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, disnake.ui.View, str, str] -
            An embed, view, resolved search term, and resolved page title.
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'user_query'
        original_query = search_query
        resolved_search_term = search_query

        try:
            if invocation_mode == 'feeling_lucky':
                quests = await get_suggestions(self, ['Quests'])
                lucky_selection = random.choice([
                    i for i in quests if not any(w in i for w in BLACKLIST_QUESTS)
                ])
                resolved_search_term = lucky_selection
                resolution_source = 'wiki_random_quest'

                page_content = parse_page(
                    BASE_URL,
                    slugify(lucky_selection),
                    HEADERS,
                    trace_id=trace_id
                )
            else:
                page_content = parse_page(
                    BASE_URL,
                    search_query,
                    HEADERS,
                    trace_id=trace_id
                )

            info = parse_infobox(page_content)
            title = parse_title(page_content)
            resolved_search_term = title

            self._log_quests_info(
                inter,
                build_log_message(
                    command='quests',
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
                log_params=build_resolved_search_log_params(
                    search_query=original_query,
                    resolved_search_term=resolved_search_term,
                    resolved_page_title=title,
                ),
            )

            if 'Quest series' not in info:
                raise exceptions.NoQuestData

            quest_details = parse_quest_details(page_content)

            embed, view = EmbedFactory().create(
                title=title,
                description=quest_details['Description'],
                colour=disnake.Colour.og_blurple(),
                thumbnail_url=THUMBNAILS['quest'],
                button_label='Quick Guide',
                button_url=f'{BASE_URL}{slugify(title)}/Quick_guide'
            )

            quest_properties = [
                'Quest series', 'Official difficulty', 'Members'
            ]

            for prop in quest_properties:
                embed.add_field(name=prop, value=info.get(prop), inline=True)

            embed.add_field(
                name='Start point',
                value=quest_details['Start point'],
                inline=False)
            embed.add_field(
                name='Requirements',
                value=f'Click [here]({BASE_URL}{slugify(title)}#Details) for a full list of requirements.',
                inline=True)
            embed.add_field(
                name='Rewards',
                value=f'Click [here]({BASE_URL}{slugify(title)}#Rewards) for a full list of rewards.',
                inline=True)
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

            return embed, view, resolved_search_term, title

        except exceptions.NoQuestData as exc:
            self._log_quests_warning(
                inter,
                build_log_message(
                    command='quests',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
                operation='search',
                trace_id=trace_id,
                search_query=original_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=title if 'title' in locals() else None,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=[
                    {'kind': 'query', 'label': 'search_query', 'value': original_query},
                    {'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term},
                    {'kind': 'page_title', 'label': 'resolved_page_title', 'value': title if 'title' in locals() else None},
                ],
                **build_expected_user_visible_failure_metadata(exc),
            )
            raise

        except exceptions.Nonexistence as exc:
            self._log_quests_warning(
                inter,
                build_log_message(
                    command='quests',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
                operation='search',
                trace_id=trace_id,
                search_query=original_query,
                resolved_search_term=resolved_search_term,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=[
                    {'kind': 'query', 'label': 'search_query', 'value': original_query},
                    {'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term},
                ],
                **build_expected_user_visible_failure_metadata(exc),
            )
            raise


    @commands.slash_command(
        name='quests',
        description='Fetch quest information from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for a quest.',
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def quests(
        self,
        inter: ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the `search_quest` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''
        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'wiki_random_quest' if invocation_mode == 'feeling_lucky' else 'user_query'
        trace_id = uuid.uuid4().hex

        self._log_quests_info(
            inter,
            build_log_message(
                command='quests',
                stage='start',
                operation='search',
            ),
            action='start',
            stage='start',
            operation='search',
            trace_id=trace_id,
            search_query=search_query,
            invocation_mode=invocation_mode,
            resolution_source=resolution_source,
            log_params=build_search_query_log_params(search_query),
        )

        try:
            await inter.response.defer()
            embed, view, resolved_search_term, resolved_page_title = await self.search_quest(
                inter,
                search_query,
                trace_id=trace_id,
            )
            await inter.followup.send(embed=embed, view=view)

            self._log_quests_success(
                inter,
                build_log_message(
                    command='quests',
                    stage='complete',
                    operation='search',
                ),
                action='complete',
                stage='complete',
                operation='search',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=resolved_page_title,
                invocation_mode=invocation_mode,
                resolution_source=resolution_source,
                log_params=build_resolved_search_log_params(
                    search_query=search_query,
                    resolved_search_term=resolved_search_term,
                    resolved_page_title=resolved_page_title,
                ),
            )
        except (exceptions.NoQuestData, exceptions.Nonexistence) as exc:
            if isinstance(exc, exceptions.Nonexistence):
                expected_description = str(exc)
            else:
                expected_description = str(exceptions.NoQuestData())
                
            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=expected_description,
                thumbnail_url=GRAYSCALE_THUMBNAILS['filler'],
                colour=0x8B8B8B,
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
            self._log_quests_error(
                inter,
                build_log_message(
                    command='quests',
                    stage='runtime_failure',
                    operation='search',
                ),
                exc,
                action='fail',
                stage='runtime_failure',
                operation='search',
                trace_id=trace_id,
                search_query=search_query,
                invocation_mode=invocation_mode,
                resolution_source=resolution_source,
                log_params=build_search_query_log_params(search_query),
                **build_unexpected_user_visible_failure_metadata(),
            )

            if inter.response.is_done():
                await inter.followup.send(
                    'Something went wrong while handling that request.',
                    ephemeral=True,
                )
            else:
                await inter.response.send_message(
                    'Something went wrong while handling that request.',
                    ephemeral=True,
                )
            return


    @quests.autocomplete('search_query')
    async def search_query_autocomplete(self, search_query: str) -> Union[List[str], str]:
        '''
        Creates a selection of autocomplete suggestions once the user begins
        typing.

        :param self: -
            Represents this object.
        :param search_query: (String) -
            Represents a search query.

        :return: (Union[List[str], str]) -
            A list of possible autocomplete suggestions,
            or "I'm feeling lucky".
        '''
        quests = await get_suggestions(self, ['Quests'])
        autocomplete_suggestions = [i for i in quests if not any(w in i for w in BLACKLIST_QUESTS)]
        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `quests` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Quests(bot))
