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

import exceptions
from config import *
from templates.bot import Bot
from utils import *

import random

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


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


    async def search_minigame(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        General function which takes the given search query and returns
        corresponding minigame data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple([discord.Embed, discord.View]) -
            An embed and view containing the minigame information.
        '''

        # Checks if the query is equal to the "I'm feeling lucky" special
        # query and returns a random article if True.
        if search_query == 'I\'m feeling lucky\u200a':
            page_content = parse_page(
                BASE_URL,
                slugify(
                    random.choice(
                        [s for s in await get_suggestions(
                            self, ['Minigames']
                        ) if s not in (
                            'Minigames',
                            'Barrows',
                            'Creature Creation'
                        )]
                    )
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
        description = parse_description(page_content).pop()
        info = parse_infobox(page_content)
        minigames = parse_page(BASE_URL, 'Minigames', HEADERS)
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
        embed.set_footer(text=f'Runebot {VER}')
        return embed, view


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
        search_query
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

        await inter.response.defer()
        embed, view = await self.search_minigame(inter, search_query)
        await inter.followup.send(embed=embed, view=view)


    @minigames.autocomplete('search_query')
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

        autocomplete_suggestions = [s for s in await get_suggestions(
            self, ['Minigames']) if s not in (
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
