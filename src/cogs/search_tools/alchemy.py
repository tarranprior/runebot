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

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

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


    async def search_alchemy(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str
    ) -> disnake.Embed:
        '''
        General function which takes the given search query and returns
        corresponding alchemy data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (discord.Embed) -
            An embed containing the alchemy information.
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

        title = parse_title(page_content)
        info = parse_infobox(page_content)
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
                HEADERS
            )
            high_price = price_data['data'][info['Item ID']]['high']

            # Gets the latest price of Nature Runes (ID: 561)
            nature_data = parse_price_data(
                f'{WIKIAPI_URL}561',
                HEADERS
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
        embed.set_footer(text=f'Runebot {VER}')
        return embed


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

        await inter.response.defer()
        embed = await self.search_alchemy(inter, search_query)
        await inter.followup.send(embed=embed)


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
