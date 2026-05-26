#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `minigames`
command, allowing users to search for minigame data from the official
Old School RuneScape wikipedia.

Classes:
    - `Minigames`: A class for handling the `minigame` command.

Key Functions:
    - `minigame(...)` and `search_query_autocomplete(...)`:
            Functions for creating a slash command and autocomplete query,
            respectively.
    - `search_minigame(...)`:
            A function for searching the Old School RuneScape wiki for minigame
            information on a specified query.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `minigame` command.

Exceptions:
    - `NoMinigameData`:
            Raised when there is no minigame data available for a given query.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import random
import uuid

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

import exceptions
from config import *
from templates.bot import Bot
from utils import *
from utils.logging import (
    BoundCommandLogger,
    build_command_log_bind,
    build_expected_user_visible_failure_metadata,
    build_log_message,
    build_resolved_search_log_params,
    build_search_query_log_params,
    build_unexpected_user_visible_failure_metadata,
)


class Minigames(commands.Cog, name='minigames'):
    '''
    A class which represents the Minigames cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Minigames class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot
        self._minigames_log = BoundCommandLogger(self._minigames_bind)


    @staticmethod
    def _invocation_source(
        inter: ApplicationCommandInteraction
    ) -> str:
        return 'slash_command'


    def _minigames_bind(
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
            command='minigames',
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

    async def search_minigame(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str,
        trace_id: str | None = None,
    ) -> Tuple[disnake.Embed, disnake.ui.View, str, str]:
        '''
        General function which takes the given search query and returns
        corresponding minigame data.

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
        resolution_source = 'wiki_random_minigame' if invocation_mode == 'feeling_lucky' else 'user_query'
        resolved_search_term = search_query

        try:
            if invocation_mode == 'feeling_lucky':
                random_selection = random.choice(
                    [s for s in await get_suggestions(
                        self, ['Minigames', 'Activities']
                    ) if s not in (
                        'Minigames',
                        'Barrows',
                        'Creature Creation'
                    )]
                )
                page_content = parse_page(
                    BASE_URL,
                    slugify(random_selection),
                    HEADERS,
                    trace_id=trace_id
                )
                resolved_search_term = random_selection
            else:
                page_content = parse_page(
                    BASE_URL,
                    search_query,
                    HEADERS,
                    trace_id=trace_id
                )

            title = parse_title(page_content)
            resolved_search_term = title

            self._minigames_log.info(
                inter,
                build_log_message(
                    command='minigames',
                    stage='resolve',
                    operation='search',
                    subject='search_query',
                    resolved=title,
                ),
                action='resolve',
                stage='resolve',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=title,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=build_resolved_search_log_params(
                    search_query=search_query,
                    resolved_search_term=resolved_search_term,
                    resolved_page_title=title,
                ),
            )

            description = parse_description(page_content).pop()
            info = parse_infobox(page_content)
            minigames = parse_page(
                BASE_URL,
                'Minigames',
                HEADERS,
                trace_id=trace_id,
            )
            thumbnail_url = parse_minigame_icon(minigames, slugify(title))

            if not thumbnail_url:
                thumbnail_url = THUMBNAILS['minigame']
                colour = 0xC24E46
            else:
                colour = disnake.Colour.from_rgb(
                    *await extract_colour(
                        self,
                        inter.guild_id,
                        inter.guild.owner_id,
                        thumbnail_url,
                        HEADERS
                    )
                )

            try:
                info['Type']
            except KeyError:
                raise exceptions.NoMinigameData

            embed, view = EmbedFactory().create(
                title=title,
                description=description,
                thumbnail_url=thumbnail_url,
                colour=colour,
                button_label='Visit Page',
                button_url=f'{BASE_URL}{slugify(title)}'
            )

            minigame_properties = [
                'Released',
                'Type',
                'Members',
                'Location',
                'Participants',
                'Reward currency',
                'Tutorial'
            ]

            for prop in minigame_properties:
                embed.add_field(name=prop, value=info.get(prop), inline=True)
            embed.add_field(name='Skills', value=info.get('Skills'), inline=False)
            embed.add_field(name='Requirements', value=info.get('Requirements'), inline=False)
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

            return embed, view, resolved_search_term, title

        except exceptions.NoMinigameData as exc:
            self._minigames_log.warning(
                inter,
                build_log_message(
                    command='minigames',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
                operation='search',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=title if 'title' in locals() else None,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=[
                    {'kind': 'query', 'label': 'search_query', 'value': search_query},
                    {'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term},
                    {'kind': 'page_title', 'label': 'resolved_page_title', 'value': title if 'title' in locals() else None},
                ],
                **build_expected_user_visible_failure_metadata(exc),
            )
            raise

        except exceptions.Nonexistence as exc:
            self._minigames_log.warning(
                inter,
                build_log_message(
                    command='minigames',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
                operation='search',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=[
                    {'kind': 'query', 'label': 'search_query', 'value': search_query},
                    {'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term},
                ],
                **build_expected_user_visible_failure_metadata(exc),
            )
            raise


    @commands.slash_command(
        name='minigames',
        description='Fetch minigame information from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for a minigame.',
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def minigames(
        self,
        inter: ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the `search_minigame` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''
        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'wiki_random_minigame' if invocation_mode == 'feeling_lucky' else 'user_query'
        trace_id = uuid.uuid4().hex

        self._minigames_log.info(
            inter,
            build_log_message(
                command='minigames',
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
            embed, view, resolved_search_term, resolved_page_title = await self.search_minigame(
                inter,
                search_query,
                trace_id=trace_id,
            )
            await inter.followup.send(embed=embed, view=view)

            self._minigames_log.success(
                inter,
                build_log_message(
                    command='minigames',
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
        except (exceptions.NoMinigameData, exceptions.Nonexistence) as exc:
            if isinstance(exc, exceptions.Nonexistence):
                expected_description = str(exc)
            else:
                expected_description = str(exceptions.NoMinigameData())

            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=expected_description,
                thumbnail_url=None,
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
            self._minigames_log.error(
                inter,
                build_log_message(
                    command='minigames',
                    stage='runtime_failure',
                    operation='search',
                ),
                exc=exc,
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

            await ack_runtime_failure(inter)
            return


    @minigames.autocomplete('search_query')
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

        autocomplete_suggestions = [s for s in await get_suggestions(
            self, ['Minigames', 'Activities']) if s not in (
            'Minigames',
            'Barrows',
            'Creature Creation'
        )]

        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `minigames` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Minigames(bot))
