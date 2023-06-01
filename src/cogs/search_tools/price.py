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
    - `search_price(...)`:
            A function for searching the Old School RuneScape wiki for price
            information on a specified query.
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

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

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


    async def search_price(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        General function which takes the given search query and returns
        exchange and value prices.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, disnake.ui.View] -
            An embed and view containing the price information.
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

        api_data = parse_price_data(
            f"{PRICEAPI_URL}{info['Item ID']}",
            HEADERS
        )

        graphapi_data = parse_price_data(
            f"{GRAPHAPI_URL}{info['Item ID']}.json",
            HEADERS
        )

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

        embed, view = EmbedFactory().create(
            title=f"{title} (ID: {info['Item ID']})",
            description=api_data['item']['description'],
            thumbnail_url=thumbnail_url,
            colour=colour,
            button_label='Real-Time Prices',
            button_url=f'https://prices.runescape.wiki/osrs/item/{info["Item ID"]}'
        )

        # Creates a button which redirects to the corresponding GE Tracker
        # (https://ge-tracker.com) page.
        ge_tracker = create_link_button(
            'GE Tracker', f'https://ge-tracker.com/item/{info["Item ID"]}')
        view.add_item(ge_tracker)
        # Creates a button which redirects to the corresponding OSRS Exchange
        # page.
        osrs_exchange = create_link_button(
            'OSRS Exchange',
            f'https://secure.runescape.com/m=itemdb_oldschool/Watermelon/viewitem?obj={info["Item ID"]}'
        )
        view.add_item(osrs_exchange)

        price_properties = ['Value', 'Exchange', 'Buy limit']
        for prop in price_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)

        try:

            # Calculating the profit margin.
            price_data = parse_price_data(
                f'{WIKIAPI_URL}{info["Item ID"]}',
                HEADERS
            )
            high_price = price_data['data'][info['Item ID']]['high']
            low_price = price_data['data'][info['Item ID']]['low']
            # Insert a + or - depending on positive or negative profit.
            def operator(i): return f'+{int(i.replace(",", ""))}' if int(i.replace(',', '')) >= 0 else '' + str(i)
            profit_margin = operator(f'{low_price +- high_price:,}')
            try:
                # Represents buy limit * profit margin.
                potential_profit = operator(
                    f'{int(info.get("Buy limit").replace(",", "")) * (int(low_price) +- int(high_price)):,}')
            except ValueError:
                # Sets the potential profit to profit margin if buy limit is
                # currently unknown.
                potential_profit = operator(
                    f'{int(profit_margin.replace("-", "").replace("+", "").replace(",", ""))}'
                )

            # Gets the last trade date/time.
            high_time = datetime.datetime.fromtimestamp(
                price_data['data'][info['Item ID']]['highTime']
            )
            low_time = datetime.datetime.fromtimestamp(
                price_data['data'][info['Item ID']]['lowTime']
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
            text=f'Runebot {VER} • Exchange data from the Grand Exchange. For more analytics, use the buttons below.'
        )
        return embed, view, filename


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
        Creates a slash command for the `search_price` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''

        await inter.response.defer()
        embed, view, filename = await self.search_price(inter, search_query)
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
