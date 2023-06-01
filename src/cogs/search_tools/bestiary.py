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

import random

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

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


    async def search_bestiary(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        General function which takes the given search query and returns
        corresponding monster data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple([discord.Embed, discord.View]) -
            An embed and view containing the bestiary information.
        '''

        # Checks if the query is equal to the "I'm feeling lucky" special
        # query and returns a random article if True.
        if search_query == 'I\'m feeling lucky\u200a':
            page_content = parse_page(
                BASE_URL,
                slugify(
                    random.choice(await get_suggestions(self, ['Monsters']))
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
        description = parse_description(page_content).pop()

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
            colour = disnake.Colour.from_rgb(
                *await extract_colour(
                    self, inter.guild_id, inter.guild.owner_id,
                    f'https://oldschool.runescape.wiki{info["Image"]}',
                    HEADERS
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
        embed.set_footer(text=f'Runebot {VER}')
        return embed, view


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
        search_query
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

        await inter.response.defer()
        embed, view = await self.search_bestiary(inter, search_query)
        await inter.followup.send(embed=embed, view=view)


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
