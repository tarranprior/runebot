#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `wikipedia`
command, allowing users to search for general article information from
the official Old School RuneScape wikipedia.

Classes:
    - `Wikipedia`:
            A class for handling the `wikipedia` command.
    - `Dropdown`:
            A class for creating dropdown options that can be added
            to a `DropdownView` instance.
    - `DropdownView`:
            A view class for creating dropdowns in the response.

Key Functions:
    - `search_wikipedia(...)`, `wikipedia(...)`, and
      `search_query_autocomplete(...)`:
            Functions for searching for and retrieving Wikipedia articles,
            as well as creating a slash command and autocomplete query for
            the `wikipedia` command.
    - `callback(self, inter: disnake.MessageInteraction)`:
            A callback function for dropdown selection.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `wikipedia` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

from config import *
from templates.bot import Bot
from utils import *


class Wikipedia(commands.Cog, name='wikipedia'):
    '''
    A class which represents the Wikipedia cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Wikipedia class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot


    async def search_wikipedia(
        self,
        inter: ApplicationCommandInteraction,
        search_query: str
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        Primary function for the `wikipedia` command which takes a search
        query and returns corresponding data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, disnake.ui.View] -
            An embed and view containing the wikipedia information.
        '''

        # Checks if the query is equal to the "I'm feeling lucky" special
        # query and returns a random article if True.
        if search_query == 'I\'m feeling lucky\u200a':
            page_content = parse_page(BASE_URL, FEELING_LUCKY, HEADERS)
        else:
            page_content = parse_page(
                BASE_URL,
                search_query,
                HEADERS
            )

        attributes = parse_all(page_content)
        title = attributes['title']
        description = attributes['description']
        infobox = attributes['infobox']
        options = attributes['options']
        thumbnail_url = attributes['thumbnail_url']

        search_query = search_query.rstrip('/')
        if 'Money making guide/' in search_query:
            button_url = f'{BASE_URL}Money_making_guide/{slugify(title)}'
        else:
            button_url = f'{BASE_URL}{slugify(title)}'

        colour = disnake.Colour.from_rgb(
            *await extract_colour(
                self,
                inter.guild_id,
                inter.guild.owner_id,
                thumbnail_url,
                HEADERS
            )
        )

        if description:
            embed, view = EmbedFactory().create(
                title=title,
                description=description.pop(),
                colour=colour, infobox=infobox,
                thumbnail_url=thumbnail_url,
                button_url=button_url
            )
            embed.set_footer(text=f'Runebot {VER}')

            if len(embed.description) < 84:
                embed.set_footer(
                    text=(f'To view more information about this page, click the button below.\nRunebot {VER}')
                )
            return embed, view

        embed = EmbedFactory().create(
            title=title,
            description=(
                f'{title} may refer to several articles. Use the dropdown below to select an option.'
            )
        )

        view = DropdownView(options)
        return embed, view


    @commands.slash_command(
        name='wikipedia',
        description='Search for an article from the official OldSchool RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for an article. Start typing for suggestions or hit `I\'m feeling lucky` for a random page!',
                type=OptionType.string,
                required=True
            ),
        ],
    )
    async def wikipedia(
        self,
        inter: disnake.ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the `search_wikipedia` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''

        await inter.response.defer()
        embed, view = await self.search_wikipedia(inter, search_query)
        await inter.followup.send(embed=embed, view=view)


    @wikipedia.autocomplete('search_query')
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

        autocomplete_suggestions = await get_wikipedia_suggestions(self)

        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


class Dropdown(disnake.ui.StringSelect):
    '''
    A class which contains logic for the dropdown options (Select Menu)
    that can be added to a `DropdownView` instance.
    '''

    def __init__(self, options: list) -> None:
        '''
        Initialises a new instance of the Dropdown class.

        :param options: (List) -
            A list of dropdown options.
        
        :return: (None)
        '''

        self.bot = Bot
        options = options

        super().__init__(
            placeholder='Select an option...',
            min_values=1,
            max_values=1,
            options=options,
        )


    async def callback(self, inter: disnake.MessageInteraction):
        '''
        The callback function for dropdown selection (Select Menu.)

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.

        :return: (None)
        '''

        await inter.response.defer()
        embed, view = await Wikipedia.search_wikipedia(
            self, inter, self.values[0]
        )
        await inter.followup.send(embed=embed, view=view)


class DropdownView(disnake.ui.View):
    '''
    A view class for creating dropdowns in the response.
    '''
    def __init__(self, options: list) -> None:
        '''
        Initialises a new instance of the DropdownView class.

        :param options: (List) -
        A list of options for the dropdown.

        :return: (None)
        '''
        self.bot = Bot
        super().__init__()
        self.add_item(Dropdown(options))


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `wikipedia` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Wikipedia(bot))
