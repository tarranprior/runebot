#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `alchemy`
command, allowing users to search for alchemy data from the official
Old School RuneScape wikipedia.

Classes:
    - `Alchemy`: A class for handling the `alchemy` command.

Key Functions:
    - `alchemy(...)` and `search_query_autocomplete(...)`:
            Functions for creating a slash command and autocomplete query,
            respectively.
    - `search_alchemy(...)`:
            A function for searching the Old School RuneScape wiki for alchemy
            information on a specified item.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `alchemy` command.

Exceptions:
    - `NoAlchemyData`:
            Raised when there is no alchemy data available for a given item.

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
    build_log_message,
    build_resolved_search_log_params,
    build_search_query_log_params,
    emit_command_log,
)

import exceptions
from templates.bot import Bot
from config import *
from utils import *


class Alchemy(commands.Cog, name='alchemy'):
    '''
    A class which represents the Alchemy cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Alchemy class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot
    
    @staticmethod
    def _invocation_source(inter: ApplicationCommandInteraction) -> str:
        return 'slash_command'


    def _alchemy_bind(
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
        item_id: str | None = None,
        **extra,
    ) -> dict:
        return build_command_log_bind(
            command='alchemy',
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
            item_id=item_id,
            **extra,
        )


    def _log_alchemy_debug(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='debug',
            bind_payload=self._alchemy_bind(inter, **bind_kwargs),
            message=message,
        )
    

    def _log_alchemy_info(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='info',
            bind_payload=self._alchemy_bind(inter, **bind_kwargs),
            message=message,
        )


    def _log_alchemy_success(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='success',
            bind_payload=self._alchemy_bind(inter, **bind_kwargs),
            message=message,
        )


    def _log_alchemy_error(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        exc: Exception,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='error',
            bind_payload=self._alchemy_bind(inter, **bind_kwargs),
            message=message,
            exc=exc,
        )
    

    def _log_alchemy_warning(
        self,
        inter: ApplicationCommandInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        emit_command_log(
            level='warning',
            bind_payload=self._alchemy_bind(inter, **bind_kwargs),
            message=message,
        )


    async def search_alchemy(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str,
        trace_id: str | None = None,
    ) -> Tuple[disnake.Embed, str, str, str]:
        '''
        General function which takes the given search query and returns
        corresponding alchemy data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, str, str, str] -
            An embed, resolved search term, resolved page title, and item ID.
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'wiki_random_item' if invocation_mode == 'feeling_lucky' else 'user_query'
        resolved_search_term = search_query

        try:
            if invocation_mode == 'feeling_lucky':
                random_selection = random.choice(
                    [i for i in await get_suggestions(self, ['Tradeable items']) if not any(w in i for w in BLACKLIST_ITEMS)]
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

            self._log_alchemy_info(
                inter,
                build_log_message(
                    command='alchemy',
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

            info = parse_infobox(page_content)
            item_id = info.get('Item ID')
            thumbnail_url = parse_thumbnail(page_content)
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
                info['Low alch']
                info['High alch']
            except KeyError:
                raise exceptions.NoAlchemyData

            embed = EmbedFactory().create(
                title=f'{title} (ID: {info.get("Item ID")})',
                description=info.get('Examine'),
                thumbnail_url=thumbnail_url,
                colour=colour
            )

            alch_properties = [
                'Value',
                'Exchange',
                'Buy limit',
                'High alch',
                'Low alch'
            ]

            for prop in alch_properties:
                embed.add_field(name=prop, value=info.get(prop), inline=True)

            try:

                # Gets the latest `high_price` of the item.
                price_data = parse_price_data(
                    f'{WIKIAPI_URL}{info["Item ID"]}',
                    HEADERS,
                    trace_id=trace_id,
                )
                high_price = price_data['data'][info['Item ID']]['high']

                # Gets the latest price of Nature Runes (ID: 561)
                nature_data = parse_price_data(
                    f'{WIKIAPI_URL}561',
                    HEADERS,
                    trace_id=trace_id,
                )
                nature_price = nature_data['data']['561']['high']

                # Calculates the profit margin.
                # Uses the latest `high_price` data and `nature_price`.
                def operator(i):
                    return f'+{str(i)}' if int(i.replace(',', '')) >= 0 else '' + str(i)
                high_alch_price = info.get("High alch")
                high_alch_price = int(high_alch_price.replace(" coins", "")
                                    .replace(" coin", "").replace(",", ""))
                profit_margin = high_alch_price - high_price - nature_price
                profit_margin = operator(f'{profit_margin:,}')

                embed.add_field(
                    name='Margin',
                    value=str(profit_margin),
                    inline=True
                )

            except KeyError:
                embed.add_field(name='Margin', value='None', inline=True)
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
            return embed, resolved_search_term, title, item_id

        except exceptions.NoAlchemyData as exc:
            self._log_alchemy_warning(
                inter,
                build_log_message(
                    command='alchemy',
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
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': title if 'title' in locals() else None,
                    },
                ],
                handled=True,
                expected_failure=True,
                user_visible=True,
                exception_type=type(exc).__name__,
                exception=str(exc),
            )
            raise

        except exceptions.Nonexistence as exc:
            self._log_alchemy_warning(
                inter,
                build_log_message(
                    command='alchemy',
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
                handled=True,
                expected_failure=True,
                user_visible=True,
                exception_type=type(exc).__name__,
                exception=str(exc),
            )
            raise


    @commands.slash_command(
        name='alchemy',
        description='Fetch alchemy data from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for an item.',
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def alchemy(
        self,
        inter: ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the `search_alchemy` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'wiki_random_item' if invocation_mode == 'feeling_lucky' else 'user_query'
        trace_id = uuid.uuid4().hex

        self._log_alchemy_info(
            inter,
            build_log_message(
                command='alchemy',
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
            embed, resolved_search_term, resolved_page_title, item_id = await self.search_alchemy(
                inter,
                search_query,
                trace_id=trace_id,
            )
            await inter.followup.send(embed=embed)

            self._log_alchemy_success(
                inter,
                build_log_message(
                    command='alchemy',
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
                item_id=item_id,
                log_params=[
                    *build_resolved_search_log_params(
                        search_query=search_query,
                        resolved_search_term=resolved_search_term,
                        resolved_page_title=resolved_page_title,
                    ),
                    {'kind': 'item', 'label': 'item_id', 'value': item_id},
                ],
            )

        except (exceptions.NoAlchemyData, exceptions.Nonexistence) as exc:
            if isinstance(exc, exceptions.Nonexistence):
                expected_description = str(exc)
            else:
                expected_description = str(exceptions.NoAlchemyData())

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
            self._log_alchemy_error(
                inter,
                build_log_message(
                    command='alchemy',
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
                handled=True,
                expected_failure=False,
                user_visible=True,
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


    @alchemy.autocomplete('search_query')
    async def search_query_autocomplete(
        self,
        search_query: str
    ) -> Union[List[str], str]:
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

        tradeable_items = await get_suggestions(self, ['Tradeable items'])
        autocomplete_suggestions = [i for i in tradeable_items if not any(w in i for w in BLACKLIST_ITEMS)]
        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `alchemy` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Alchemy(bot))
