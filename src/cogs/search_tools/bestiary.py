#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `bestiary`
command, allowing users to search for monster data from the official
Old School RuneScape wikipedia.

Classes:
    - `Bestiary`: A class for handling the `bestiary` command.

Key Functions:
    - `bestiary(...)` and `search_query_autocomplete(...)`:
            Functions for creating a slash command and autocomplete query,
            respectively.
    - `search_bestiary(...)`:
            A function for searching the Old School RuneScape wiki for bestiary
            information on a specified query.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `bestiary` command.

Exceptions:
    - `NoMonsterData`:
            Raised when there is no bestiary data available for a given query.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import asyncio
import random
import time
import uuid

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType
from utils.logging import (
    BoundCommandLogger,
    build_command_log_bind,
    build_expected_user_visible_failure_metadata,
    log_colour_extraction_failure,
    build_log_message,
    build_resolved_search_log_params,
    build_search_query_log_params,
    build_unexpected_user_visible_failure_metadata,
    elapsed_ms,
)

import exceptions
from config import *
from templates.bot import Bot
from utils import *


class Bestiary(commands.Cog, name='bestiary'):
    '''
    A class which represents the Bestiary cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Bestiary class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot
        self._bestiary_log = BoundCommandLogger(self._bestiary_bind)

    @staticmethod
    def _invocation_source(
        inter: ApplicationCommandInteraction
    ) -> str:
        return 'slash_command'


    def _bestiary_bind(
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
        monster_id: str | None = None,
        **extra,
    ) -> dict:
        return build_command_log_bind(
            command='bestiary',
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
            monster_id=monster_id,
            **extra,
        )

    async def search_bestiary(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str,
        trace_id: str | None = None,
        started_at: float | None = None,
    ) -> Tuple[disnake.Embed, disnake.ui.View, str, str, str]:
        '''
        General function which takes the given search query and returns
        corresponding monster data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, disnake.ui.View, str, str, str] -
            An embed, view, resolved search term, resolved page title, and monster ID.
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'wiki_random_monster' if invocation_mode == 'feeling_lucky' else 'user_query'
        resolved_search_term = search_query

        try:
            if invocation_mode == 'feeling_lucky':
                random_selection = random.choice(await get_suggestions(self, ['Monsters']))
                page_content = await asyncio.to_thread(
                    parse_page,
                    BASE_URL,
                    slugify(random_selection),
                    HEADERS,
                    trace_id=trace_id
                )
                resolved_search_term = random_selection
            else:
                page_content = await asyncio.to_thread(
                    parse_page,
                    BASE_URL,
                    search_query,
                    HEADERS,
                    trace_id=trace_id
                )

            info = parse_infobox(page_content)
            monster_id = info.get('Monster ID')
            title = parse_title(page_content)
            resolved_search_term = title
            description = parse_description(page_content).pop()

            self._bestiary_log.info(
                inter,
                build_log_message(
                    command='bestiary',
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

            try:
                info['Combat level']
            except KeyError:
                raise exceptions.NoMonsterData

            embed, view = EmbedFactory().create(
                title=title,
                description=description,
                thumbnail_url=f'https://oldschool.runescape.wiki{info["Image"]}',
                button_label='Visit Page',
                button_url=f'{BASE_URL}{slugify(title)}'
            )

            try:
                image_url = f'https://oldschool.runescape.wiki{info["Image"]}'

                colour = disnake.Colour.from_rgb(
                    *await extract_colour(
                        self, inter.guild_id, inter.guild.owner_id,
                        image_url,
                        HEADERS,
                        on_failure=lambda exc: log_colour_extraction_failure(
                            self._bestiary_log,
                            inter,
                            'bestiary',
                            image_url,
                            exc,
                            trace_id=trace_id,
                            log_params=[{'kind': 'monster', 'label': 'monster_id', 'value': monster_id}],
                            search_query=search_query,
                            resolved_search_term=resolved_search_term,
                            resolved_page_title=title,
                            resolution_source=resolution_source,
                            invocation_mode=invocation_mode,
                            monster_id=monster_id,
                        ),
                    )
                )
                embed.colour = colour
            except KeyError:
                pass

            monster_properties = [
                'Aggressive',
                'Poison',
                'Venom',
                'Cannons',
                'Thralls',
                'Attack style',
                'Poisonous',
                'Respawn time'
            ]

            embed.add_field(
                name='Examine',
                value=info.get('Examine'),
                inline=False
            )
            embed.add_field(
                name='Combat level',
                value=info.get('Combat level'),
                inline=True
            )
            embed.add_field(
                name='Max hit',
                value=')\n'.join(info.get('Max hit').split(')')),
                inline=True
            )

            for prop in monster_properties:
                prop_value = info.get(prop)
                if prop_value is not None:
                    embed.add_field(name=prop, value=prop_value, inline=True)
                else:
                    embed.add_field(name=prop, value='N/A', inline=True)

            embed.add_field(
                name='Monster ID(s)',
                value=f'```\n{", ".join(info.get("Monster ID").split(","))}```',
                inline=False)
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
            return embed, view, resolved_search_term, title, monster_id

        except exceptions.NoMonsterData as exc:
            self._bestiary_log.warning(
                inter,
                build_log_message(
                    command='bestiary',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
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
                **({'duration_ms': elapsed_ms(started_at)} if started_at is not None else {}),
            )
            raise

        except exceptions.Nonexistence as exc:
            self._bestiary_log.warning(
                inter,
                build_log_message(
                    command='bestiary',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
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
                **({'duration_ms': elapsed_ms(started_at)} if started_at is not None else {}),
            )
            raise


    @commands.slash_command(
        name='bestiary',
        description='Fetch monster information from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for a monster.',
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def bestiary(
        self,
        inter: ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the `search_bestiary` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'wiki_random_monster' if invocation_mode == 'feeling_lucky' else 'user_query'
        trace_id = uuid.uuid4().hex
        started_at = time.perf_counter()

        self._bestiary_log.info(
            inter,
            build_log_message(
                command='bestiary',
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
            embed, view, resolved_search_term, resolved_page_title, monster_id = await self.search_bestiary(
                inter,
                search_query,
                trace_id=trace_id,
                started_at=started_at,
            )
            await inter.followup.send(embed=embed, view=view)

            self._bestiary_log.success(
                inter,
                build_log_message(
                    command='bestiary',
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
                monster_id=monster_id,
                duration_ms=elapsed_ms(started_at),
                log_params=[
                    *build_resolved_search_log_params(
                        search_query=search_query,
                        resolved_search_term=resolved_search_term,
                        resolved_page_title=resolved_page_title,
                    ),
                    {'kind': 'monster', 'label': 'monster_id', 'value': monster_id},
                ],
            )
        except (exceptions.NoMonsterData, exceptions.Nonexistence) as exc:
            if isinstance(exc, exceptions.Nonexistence):
                expected_description = str(exc)
            else:
                expected_description = str(exceptions.NoMonsterData())

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
            self._bestiary_log.error(
                inter,
                build_log_message(
                    command='bestiary',
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
                duration_ms=elapsed_ms(started_at),
                **build_unexpected_user_visible_failure_metadata(),
            )

            await ack_runtime_failure(inter)
            return


    @bestiary.autocomplete('search_query')
    async def search_query_autocomplete(self, search_query: str) -> Union[List[str], str]:
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

        autocomplete_suggestions = await get_suggestions(self, ['Monsters'])
        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `bestiary` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Bestiary(bot))
