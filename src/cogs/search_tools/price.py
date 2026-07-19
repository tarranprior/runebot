#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `price`
command, which allows users to search for price data from various APIs.

Classes:
    - `Price`: A class for handling the `price` command.

Key Functions:
    - `price(...)` and `search_query_autocomplete(...)`:
            Functions for creating a slash command and autocomplete query,
            respectively.
    - `_resolve_item_info(...)`:
            Resolves a search query to item information including item ID.
    - `_build_price_embed(...)`:
            Builds the price embed, view, and graph from an item ID.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `price` command.

Exceptions:
    - `NoPriceData`:
            Raised when there is no price data available for a given query.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import datetime as dt
import random
import uuid
from typing import Tuple, Union, List

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType, MessageInteraction

import exceptions
from config import *
from templates.bot import Bot
from utils import *
from utils.logging import (
    BoundCommandLogger,
    build_command_log_bind,
    build_log_message,
    log_colour_extraction_failure,
)


class Price(commands.Cog, name='price'):
    '''
    A class which represents the Price cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Price class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot
        self._price_log = BoundCommandLogger(self._price_bind)


    @staticmethod
    def _invocation_source(inter: ApplicationCommandInteraction | MessageInteraction) -> str:
        return (
            'component_callback'
            if isinstance(inter, MessageInteraction)
            else 'slash_command'
        )


    def _price_bind(
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
        item_id: str | None = None,
        component_type: str | None = None,
        button_action: str | None = None,
        owner_id: str | int | None = None,
        **extra,
    ) -> dict:
        normalized_owner_id = str(owner_id) if owner_id is not None else None
        return build_command_log_bind(
            command='price',
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
            component_type=component_type,
            button_action=button_action,
            owner_id=normalized_owner_id,
            **extra,
        )


    def _cleanup_price_artifact(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        *,
        file: disnake.File,
        artifact_path: str,
        trace_id: str | None,
        send_succeeded: bool,
        search_query: str | None = None,
        invocation_mode: str | None = None,
        resolution_source: str | None = None,
        item_id: str | None = None,
        owner_id: str | int | None = None,
        component_type: str | None = None,
        button_action: str | None = None,
    ) -> None:
        cleanup_errors = {}

        try:
            file.close()
        except Exception as exc:
            cleanup_errors['close_exception_type'] = type(exc).__name__
            cleanup_errors['close_exception'] = str(exc)

        try:
            os.remove(artifact_path)
        except Exception as exc:
            cleanup_errors['remove_exception_type'] = type(exc).__name__
            cleanup_errors['remove_exception'] = str(exc)

        if cleanup_errors:
            self._price_log.debug(
                inter,
                '<artifact>: <cleanup> failure.',
                action='fail',
                stage='failure',
                operation='artifact_cleanup',
                trace_id=trace_id,
                search_query=search_query,
                invocation_mode=invocation_mode,
                resolution_source=resolution_source,
                item_id=item_id,
                owner_id=owner_id,
                component_type=component_type,
                button_action=button_action,
                handled=True,
                expected_failure=False,
                user_visible=False,
                fatal=False,
                artifact_type='price_graph',
                artifact_path=artifact_path,
                send_succeeded=send_succeeded,
                **cleanup_errors,
            )


    async def _ack_invalid_price_component(self, inter: MessageInteraction) -> None:
        await ack_component_failure(
            inter,
            self._price_log,
            'price',
            description=f'This price control is no longer valid. Please run {SLASH_MENTIONS["price"]} again.',
            operation='invalid_component',
            invocation_source=self._invocation_source(inter),
        )


    def _validate_price_info(self, info: dict) -> None:
        try:
            info['Value']
            info['Exchange']
            info['Buy limit']
        except KeyError as exc:
            raise exceptions.NoPriceData from exc


    async def _resolve_item_info(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str,
        trace_id: str | None = None,
        lucky_selection: str | None = None,
    ) -> Tuple[dict, str, str]:
        '''
        Resolves a search query to item information and resolved page metadata.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[dict, str, str] -
            A tuple containing the item info dictionary, resolved search term,
            and resolved page title.
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolution_source = 'wiki_random_item' if invocation_mode == 'feeling_lucky' else 'user_query'
        resolved_search_term = search_query

        try:
            if invocation_mode == 'feeling_lucky':
                random_selection = lucky_selection or random.choice(
                    [i for i in await get_suggestions(self, ['Tradeable items']) if not any(w in i for w in BLACKLIST_ITEMS)]
                )
                resolved_search_term = random_selection
                page_content = parse_page(
                    BASE_URL,
                    slugify(random_selection),
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

            title = parse_title(page_content)
            resolved_search_term = title

            self._price_log.info(
                inter,
                build_log_message(
                    command='price',
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
                log_params=[
                    {'kind': 'query', 'label': 'search_query', 'value': search_query},
                    {'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term},
                    {'kind': 'page_title', 'label': 'resolved_page_title', 'value': title},
                ],
            )

            info = parse_infobox(page_content)
            self._validate_price_info(info)

            return info, resolved_search_term, title

        except exceptions.NoPriceData as exc:
            self._price_log.warning(
                inter,
                build_log_message(
                    command='price',
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

        except (exceptions.Nonexistence, exceptions.WikiRequestFailed) as exc:
            self._price_log.warning(
                inter,
                build_log_message(
                    command='price',
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


    def _resolve_item_info_by_id(
        self,
        item_id: str,
        trace_id: str | None = None,
    ) -> Tuple[dict, dict, str]:
        api_data = parse_price_data(
            f"{PRICEAPI_URL}{item_id}",
            HEADERS,
            trace_id=trace_id,
        )

        item = api_data.get('item') if isinstance(api_data, dict) else None
        item_name = item.get('name') if isinstance(item, dict) else None

        if not isinstance(item_name, str) or not item_name.strip():
            raise exceptions.NoPriceData

        page_content = parse_page(
            BASE_URL,
            slugify(item_name),
            HEADERS,
            trace_id=trace_id,
        )
        info = parse_infobox(page_content)
        title = parse_title(page_content)

        self._validate_price_info(info)

        return api_data, info, title


    def _build_price_view(
        self,
        item_id: str,
        owner_id: int
    ) -> disnake.ui.View:
        '''
        Builds the view with all buttons for the price command.

        :param self: -
            Represents this object.
        :param item_id: (String) -
            Represents the item ID.
        :param owner_id: (Integer) -
            Represents the user ID who initiated the command.

        :return: (disnake.ui.View) -
            A view containing all price-related buttons.
        '''

        view = disnake.ui.View(timeout=None)
        
        realtime_prices = create_link_button(
            'Real-Time Prices',
            f'https://prices.runescape.wiki/osrs/item/{item_id}'
        )
        view.add_item(realtime_prices)

        ge_tracker = create_link_button(
            'GE Tracker',
            f'https://ge-tracker.com/item/{item_id}'
        )
        view.add_item(ge_tracker)

        osrs_exchange = create_link_button(
            'OSRS Exchange',
            f'https://secure.runescape.com/m=itemdb_oldschool/Watermelon/viewitem?obj={item_id}'
        )
        view.add_item(osrs_exchange)

        refresh_button = disnake.ui.Button(
            label='⟳',
            style=disnake.ButtonStyle.secondary,
            custom_id=f'price:refresh:{item_id}:{owner_id}',
            row=1
        )
        view.add_item(refresh_button)

        return view


    async def _build_price_embed(
        self,
        item_id: str,
        inter: ApplicationCommandInteraction | MessageInteraction,
        owner_id: int,
        *,
        api_data: dict,
        info: dict,
        title: str,
        trace_id: str | None = None,
    ) -> Tuple[disnake.Embed, disnake.ui.View, str]:
        '''
        Builds the price embed, view, and graph from an item ID.

        :param self: -
            Represents this object.
        :param item_id: (String) -
            Represents the item ID.
        :param inter: (ApplicationCommandInteraction | MessageInteraction) -
            Represents an interaction.
        :param owner_id: (Integer) -
            Represents the user ID who initiated the command.

        :return: Tuple[disnake.Embed, disnake.ui.View, str] -
            An embed, view, and filename containing the price information.
        '''

        graphapi_data = parse_price_data(
            f"{GRAPHAPI_URL}{item_id}.json",
            HEADERS,
            trace_id=trace_id,
        )

        filename = await generate_graph(graphapi_data)

        thumbnail_url = api_data['item']['icon_large']

        colour = disnake.Colour.from_rgb(
            *await extract_colour(
                self,
                inter.guild_id,
                inter.guild.owner_id,
                thumbnail_url,
                HEADERS,
                on_failure=lambda exc: log_colour_extraction_failure(
                    self._price_log,
                    inter,
                    'price',
                    thumbnail_url,
                    exc,
                    trace_id=trace_id,
                    log_params=[{'kind': 'item', 'label': 'item_id', 'value': item_id}],
                    item_id=item_id,
                    thumbnail_url=thumbnail_url,
                ),
            )
        )

        view = self._build_price_view(item_id, owner_id)
        embed = disnake.Embed(
            title=f"{title} (ID: {item_id})",
            description=api_data['item']['description'],
            colour=colour
        )
        embed.set_thumbnail(url=thumbnail_url)

        price_properties = ['Value', 'Exchange', 'Buy limit']
        for prop in price_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)

        try:
            # Calculating the profit margin.
            price_data = parse_price_data(
                f'{WIKIAPI_URL}{item_id}',
                HEADERS,
                trace_id=trace_id,
            )
            high_price = price_data['data'][item_id]['high']
            low_price = price_data['data'][item_id]['low']
            # Insert a + or - depending on positive or negative profit.
            def operator(i): return f'+{int(i.replace(",", ""))}' if int(i.replace(',', '')) >= 0 else '' + str(i)
            profit_margin = operator(f'{low_price - high_price:,}')
            
            buy_limit_value = info.get("Buy limit")
            try:
                if not isinstance(buy_limit_value, str):
                    raise ValueError

                buy_limit = int(buy_limit_value.replace(",", ""))
                potential_profit = operator(
                    f'{buy_limit * (int(low_price) - int(high_price)):,}'
                )
            except (ValueError, AttributeError):
                potential_profit = operator(
                    f'{int(profit_margin.replace("-", "").replace("+", "").replace(",", ""))}'
                )

            # Gets the last trade date/time.
            high_time = dt.datetime.fromtimestamp(
                price_data['data'][item_id]['highTime']
            )
            low_time = dt.datetime.fromtimestamp(
                price_data['data'][item_id]['lowTime']
            )
            present_time = dt.datetime.now().replace(microsecond=0)
            high_date_diff = convert_date_to_duration(present_time, high_time)
            low_date_diff = convert_date_to_duration(present_time, low_time)

        except KeyError:
            raise exceptions.NoPriceData

        embed.add_field(
            name='Buy price',
            value=f'{high_price:,} coins\n`{high_date_diff}`',
            inline=True
        )
        embed.add_field(
            name='Sell price',
            value=f'{low_price:,} coins\n`{low_date_diff}`',
            inline=True
        )
        embed.add_field(
            name='Margin',
            value=f'{profit_margin}\n(`{potential_profit}`)',
            inline=True
        )

        embed.add_field(
            name='Today',
            value=f'{api_data["item"]["today"]["price"]} coins ({api_data["item"]["today"]["trend"].title()})'.replace('- ', '-'),
            inline=False
        )
        embed.add_field(
            name='30 Days',
            value=f'{api_data["item"]["day30"]["change"]}',
            inline=True
        )
        embed.add_field(
            name='90 Days',
            value=f'{api_data["item"]["day90"]["change"]}',
            inline=True
        )
        embed.add_field(
            name='180 Days',
            value=f'{api_data["item"]["day180"]["change"]}',
            inline=True
        )
        embed.set_footer(
            text=(
                f'Exchange data from the official Grand Exchange API\n'
                f'Runebot {DISPLAY_VERSION}'
            )
        )

        embed.timestamp = inter.created_at
        return embed, view, filename


    @commands.Cog.listener('on_button_click')
    async def on_button_click(
        self,
        inter: MessageInteraction
    ) -> None:
        '''
        Cog listener which handles button clicks for /price refresh.

        :param self: -
            Represents this object.
        :param inter: (disnake.MessageInteraction) -
            Represents a message component interaction triggered by a button.

        :return: (None)
        '''

        custom_id = inter.component.custom_id

        if not custom_id or not custom_id.startswith('price:'):
            return

        payload = custom_id.removeprefix('price:')
        parts = payload.split(':')

        if len(parts) != 3:
            await self._ack_invalid_price_component(inter)
            return

        action, item_id, owner_id = parts

        if action != 'refresh':
            await self._ack_invalid_price_component(inter)
            return
        
        if str(inter.author.id) != owner_id:
            await ack_wrong_component_user(inter, self._price_log, 'price')
            return

        trace_id = uuid.uuid4().hex
        loading_view = build_loading_button_view(inter)
        await inter.response.edit_message(view=loading_view)

        self._price_log.info(
            inter,
            build_log_message(
                command='price',
                stage='start',
                operation='refresh',
            ),
            action='start',
            stage='start',
            operation='refresh',
            trace_id=trace_id,
            component_type='button',
            button_action='refresh',
            item_id=item_id,
            owner_id=owner_id,
            log_params=[
                {'kind': 'item', 'label': 'item_id', 'value': item_id},
            ],
        )

        try:
            api_data, info, title = self._resolve_item_info_by_id(
                item_id,
                trace_id=trace_id,
            )

            self._price_log.info(
                inter,
                build_log_message(
                    command='price',
                    stage='resolve',
                    operation='refresh',
                    subject='item_id',
                    resolved=title,
                ),
                action='resolve',
                stage='resolve',
                operation='refresh',
                trace_id=trace_id,
                component_type='button',
                button_action='refresh',
                item_id=item_id,
                owner_id=owner_id,
                resolved_page_title=title,
                log_params=[
                    {'kind': 'item', 'label': 'item_id', 'value': item_id},
                    {'kind': 'page_title', 'label': 'resolved_page_title', 'value': title},
                ],
            )

            embed, view, filename = await self._build_price_embed(
                item_id,
                inter,
                int(owner_id),
                api_data=api_data,
                info=info,
                title=title,
                trace_id=trace_id,
            )

            artifact_path = f'artifacts/{filename}'
            file = disnake.File(artifact_path, filename=filename)
            embed.set_image(url=f'attachment://{filename}')

            send_succeeded = False
            try:
                await inter.edit_original_response(
                    embed=embed,
                    view=view,
                    attachments=[],
                    file=file
                )
                send_succeeded = True
            finally:
                self._cleanup_price_artifact(
                    inter,
                    file=file,
                    artifact_path=artifact_path,
                    trace_id=trace_id,
                    send_succeeded=send_succeeded,
                    item_id=item_id,
                    owner_id=owner_id,
                    component_type='button',
                    button_action='refresh',
                )

            self._price_log.success(
                inter,
                build_log_message(
                    command='price',
                    stage='complete',
                    operation='refresh',
                ),
                action='complete',
                stage='complete',
                operation='refresh',
                trace_id=trace_id,
                component_type='button',
                button_action='refresh',
                item_id=item_id,
                owner_id=owner_id,
                log_params=[
                    {'kind': 'item', 'label': 'item_id', 'value': item_id},
                ],
            )

        except (
            exceptions.NoPriceData,
            exceptions.Nonexistence,
            exceptions.WikiRequestFailed,
        ) as exc:
            if isinstance(exc, (exceptions.Nonexistence, exceptions.WikiRequestFailed)):
                expected_description = str(exc)
            else:
                expected_description = str(exceptions.NoPriceData())
            colour = 0xB72615 if isinstance(exc, exceptions.WikiRequestFailed) else 0x8B8B8B

            self._price_log.warning(
                inter,
                build_log_message(
                    command='price',
                    stage='failure',
                    operation='refresh',
                ),
                action='fail',
                stage='failure',
                operation='refresh',
                trace_id=trace_id,
                component_type='button',
                button_action='refresh',
                item_id=item_id,
                owner_id=owner_id,
                log_params=[{'kind': 'item', 'label': 'item_id', 'value': item_id}],
                handled=True,
                expected_failure=True,
                user_visible=True,
                exception_type=type(exc).__name__,
                exception=str(exc),
            )

            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=expected_description,
                thumbnail_url=None,
                colour=colour,
                button_label='Support Server',
                button_url=SUPPORT_SERVER
            )
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
            await inter.edit_original_response(embed=embed, view=view, attachments=[])

        except Exception as exc:
            self._price_log.error(
                inter,
                build_log_message(
                    command='price',
                    stage='runtime_failure',
                    operation='refresh',
                ),
                exc=exc,
                action='fail',
                stage='runtime_failure',
                operation='refresh',
                trace_id=trace_id,
                component_type='button',
                button_action='refresh',
                item_id=item_id,
                owner_id=owner_id,
                handled=True,
                expected_failure=False,
                user_visible=True,
            )
            view = self._build_price_view(item_id, int(owner_id))
            await inter.edit_original_response(view=view)
            await ack_runtime_failure(inter)
            return


    @commands.slash_command(
        name='price',
        description='Fetch guide price data from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for an item.',
                type=OptionType.string,
                required=True
            )
        ],
    )
    async def price(
        self,
        inter: ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the price lookup function.

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

        self._price_log.info(
            inter,
            build_log_message(
                command='price',
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
            log_params=[{'kind': 'query', 'label': 'search_query', 'value': search_query}],
        )

        try:
            lucky_selection = None
            if invocation_mode == 'feeling_lucky':
                lucky_selection = random.choice(
                    [i for i in await get_suggestions(self, ['Tradeable items']) if not any(w in i for w in BLACKLIST_ITEMS)]
                )

            await inter.response.defer()
            info, resolved_search_term, resolved_page_title = await self._resolve_item_info(
                inter,
                search_query,
                trace_id=trace_id,
                lucky_selection=lucky_selection,
            )
            item_id = info['Item ID']
            api_data = parse_price_data(
                f"{PRICEAPI_URL}{item_id}",
                HEADERS,
                trace_id=trace_id,
            )

            embed, view, filename = await self._build_price_embed(
                item_id,
                inter,
                inter.author.id,
                api_data=api_data,
                info=info,
                title=resolved_page_title,
                trace_id=trace_id,
            )

            artifact_path = f'artifacts/{filename}'
            file = disnake.File(artifact_path, filename=filename)
            embed.set_image(url=f'attachment://{filename}')

            send_succeeded = False
            try:
                await inter.followup.send(embed=embed, view=view, file=file)
                send_succeeded = True
            finally:
                self._cleanup_price_artifact(
                    inter,
                    file=file,
                    artifact_path=artifact_path,
                    trace_id=trace_id,
                    send_succeeded=send_succeeded,
                    search_query=search_query,
                    invocation_mode=invocation_mode,
                    resolution_source=resolution_source,
                )

            self._price_log.success(
                inter,
                build_log_message(
                    command='price',
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
                    {'kind': 'query', 'label': 'search_query', 'value': search_query},
                    {'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term},
                    {'kind': 'page_title', 'label': 'resolved_page_title', 'value': resolved_page_title},
                    {'kind': 'item', 'label': 'item_id', 'value': item_id},
                ],
            )
        except (
            exceptions.NoPriceData,
            exceptions.Nonexistence,
            exceptions.WikiRequestFailed,
        ) as exc:
            if isinstance(exc, (exceptions.Nonexistence, exceptions.WikiRequestFailed)):
                expected_description = str(exc)
            else:
                expected_description = str(exceptions.NoPriceData())
            colour = 0xB72615 if isinstance(exc, exceptions.WikiRequestFailed) else 0x8B8B8B

            if 'item_id' in locals():
                log_params = [
                    {'kind': 'query', 'label': 'search_query', 'value': search_query},
                ]
                if 'resolved_search_term' in locals():
                    log_params.append({'kind': 'query', 'label': 'resolved_search_term', 'value': resolved_search_term})
                if 'resolved_page_title' in locals():
                    log_params.append({'kind': 'page_title', 'label': 'resolved_page_title', 'value': resolved_page_title})
                log_params.append({'kind': 'item', 'label': 'item_id', 'value': item_id})

                self._price_log.warning(
                    inter,
                    build_log_message(
                        command='price',
                        stage='failure',
                        operation='search',
                    ),
                    action='fail',
                    stage='failure',
                    operation='search',
                    trace_id=trace_id,
                    search_query=search_query,
                    invocation_mode=invocation_mode,
                    resolution_source=resolution_source,
                    handled=True,
                    expected_failure=True,
                    user_visible=True,
                    exception_type=type(exc).__name__,
                    exception=str(exc),
                    **({'resolved_search_term': resolved_search_term} if 'resolved_search_term' in locals() else {}),
                    **({'resolved_page_title': resolved_page_title} if 'resolved_page_title' in locals() else {}),
                    **({'item_id': item_id} if 'item_id' in locals() else {}),
                    log_params=log_params,
                )

            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=expected_description,
                thumbnail_url=None,
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
            self._price_log.error(
                inter,
                build_log_message(
                    command='price',
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
                log_params=[{'kind': 'query', 'label': 'search_query', 'value': search_query}],
                handled=True,
                expected_failure=False,
                user_visible=True,
            )
            await ack_runtime_failure(inter)
            return

    @price.autocomplete('search_query')
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

        tradeable_items = await get_suggestions(self, ['Tradeable items'])
        autocomplete_suggestions = [i for i in tradeable_items if not any(w in i for w in BLACKLIST_ITEMS)]
        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `price` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Price(bot))
