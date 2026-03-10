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

import datetime
import random
from typing import Tuple, Union, List

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType, MessageInteraction

from config import *
from templates.bot import Bot
from utils import *


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


    async def _resolve_item_info(self, search_query: str) -> Tuple[dict, str]:
        '''
        Resolves a search query to item information including item ID and title.

        :param self: -
            Represents this object.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[dict, str] -
            A tuple containing the item info dictionary and title.
        '''

        # Checks if the query is equal to the "I'm feeling lucky" special
        # query and returns a random article if True.
        if search_query == 'I\'m feeling lucky\u200a':
            tradeable_items = await get_suggestions(self, ['Tradeable items'])
            page_content = parse_page(
                BASE_URL,
                slugify(
                    random.choice([i for i in tradeable_items if not any(w in i for w in BLACKLIST_ITEMS)])
                ),
                HEADERS
            )
        else:
            page_content = parse_page(
                BASE_URL,
                search_query,
                HEADERS
            )

        info = parse_infobox(page_content)
        title = parse_title(page_content)

        try:
            info['Value']
            info['Exchange']
            info['Buy limit']
        except KeyError:
            raise exceptions.NoPriceData

        return info, title


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
        owner_id: int
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

        # Fetch price data from APIs
        api_data = parse_price_data(
            f"{PRICEAPI_URL}{item_id}",
            HEADERS
        )

        graphapi_data = parse_price_data(
            f"{GRAPHAPI_URL}{item_id}.json",
            HEADERS
        )

        # Fetch item info to get title and other properties
        page_content = parse_page(
            BASE_URL,
            slugify(api_data['item']['name']),
            HEADERS
        )
        info = parse_infobox(page_content)
        title = parse_title(page_content)

        filename = await generate_graph(graphapi_data)

        thumbnail_url = api_data['item']['icon_large']
        colour = disnake.Colour.from_rgb(
            *await extract_colour(
                self,
                inter.guild_id,
                inter.guild.owner_id,
                thumbnail_url,
                HEADERS
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
                HEADERS
            )
            high_price = price_data['data'][item_id]['high']
            low_price = price_data['data'][item_id]['low']
            # Insert a + or - depending on positive or negative profit.
            def operator(i): return f'+{int(i.replace(",", ""))}' if int(i.replace(',', '')) >= 0 else '' + str(i)
            profit_margin = operator(f'{low_price - high_price:,}')
            try:
                # Represents buy limit * profit margin.
                potential_profit = operator(
                    f'{int(info.get("Buy limit").replace(",", "")) * (int(low_price) - int(high_price)):,}'
                )
            except ValueError:
                # Sets the potential profit to profit margin if buy limit is
                # currently unknown.
                potential_profit = operator(
                    f'{int(profit_margin.replace("-", "").replace("+", "").replace(",", ""))}'
                )

            # Gets the last trade date/time.
            high_time = datetime.datetime.fromtimestamp(
                price_data['data'][item_id]['highTime']
            )
            low_time = datetime.datetime.fromtimestamp(
                price_data['data'][item_id]['lowTime']
            )
            present_time = datetime.datetime.now().replace(microsecond=0)
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
                f'Runebot {VER}'
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
            return

        action, item_id, owner_id = parts

        if action != 'refresh':
            return
        
        if str(inter.author.id) != owner_id:
            await inter.response.send_message(
                'Only the original author can use these buttons.',
                ephemeral=True
            )
            return

        loading_view = build_loading_button_view(inter)
        await inter.response.edit_message(view=loading_view)

        try:
            embed, view, filename = await self._build_price_embed(
                item_id,
                inter,
                int(owner_id)
            )

            file = disnake.File(f'assets/{filename}', filename=filename)
            embed.set_image(url=f'attachment://{filename}')

            await inter.edit_original_response(
                embed=embed,
                view=view,
                attachments=[],
                file=file
            )

            file.close()
            os.remove(f'assets/{filename}')

        except Exception as exc:
            view = self._build_price_view(item_id, int(owner_id))
            await inter.edit_original_response(view=view)
            await inter.followup.send(
                "An error occurred while refreshing the price data.",
                ephemeral=True
            )
            raise exc


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

        await inter.response.defer()

        info, title = await self._resolve_item_info(search_query)
        item_id = info['Item ID']

        embed, view, filename = await self._build_price_embed(
            item_id,
            inter,
            inter.author.id
        )

        file = disnake.File(f'assets/{filename}', filename=filename)
        embed.set_image(url=f'attachment://{filename}')
        await inter.followup.send(embed=embed, view=view, file=file)
        file.close()
        os.remove(f'assets/{filename}')


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
