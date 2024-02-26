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

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

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


    async def search_quest(
        self,
        search_query: str
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        Primary function for the `quests` command which takes a search
        query and returns corresponding quest data.
    
        :param self: -
            Represents this object.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, disnake.ui.View] -
            An embed and view containing the quest information.
        '''

        # Checks if the query is equal to the "I'm feeling lucky" special
        # query and returns a random article if True.
        if search_query == 'I\'m feeling lucky\u200a':
            quests = await get_suggestions(self, ['Quests'])
            page_content = parse_page(
                BASE_URL,
                slugify(
                    random.choice([i for i in quests if not any(w in i for w in BLACKLIST_QUESTS)])
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
            info['Quest series']
        except KeyError:
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
        embed.set_footer(text=f'Runebot {VER}')
        return embed, view


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
        search_query
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
        await inter.response.defer()
        embed, view = await self.search_quest(search_query)
        await inter.followup.send(embed=embed, view=view)


    @quests.autocomplete('search_query')
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
