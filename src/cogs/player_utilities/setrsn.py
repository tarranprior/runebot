#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `setrsn`
command, allowing users to save a RuneScape username for their
Discord account.

Classes:
    - `Setrsn`:
            A class for handling the `setrsn` command.

Key Functions:
    - `set_username(...)`, `setrsn(...)`:
            Functions for setting a RuneScape username, as well as
            creating a slash command and autocomplete query for the `setrsn`
            command.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `setrsn` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *


class Setrsn(commands.Cog, name='setrsn'):
    '''
    A class which represents the Setrsn cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises the Setrsn cog.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        return: (None)
        '''
        self.bot = bot


    async def set_username(
        self,
        inter: ApplicationCommandInteraction,
        username: str,
        account_type: str = None
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        Function which takes a provided username and stores it
        with a respective user_id for easy retrieval.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param username: (String) -
            Represents a player's username.
        :param account_type: (String[Optional]) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)

        :return: (Tuple[disnake.Embed, disnake.ui.View])
            An embed and view containing a success message.
        '''

        if len(username) > MAX_CHARS or any(char in username for char in BLACKLIST_CHARS):
            raise exceptions.UsernameInvalid

        if not account_type:
            account_type = 'Normal'

        if await get_username(self, inter.author.id):
            await remove_username(self, inter.author.id)
        await add_username(self, inter.author.id, username, account_type)

        embed, view = EmbedFactory().create(
            title=f'Username has been set.',
            description=f'Your username has now been set to **{username}**.\n\n'
            'You can make changes to your username at any time by using '
            '`/setrsn`, or use `/unsetrsn` to remove it entirely. '
            'Toggle more options with `/settings`.',
            button_label='Visit Hiscores',
            button_url=f'{HISCORE_URLS.get(account_type)}{slugify(username)}'
        )
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'Runebot {VER}')

        return embed, view


    @commands.slash_command(
        name='setrsn',
        description='Set a RuneScape username for your Discord account.',
        options=[
            Option(
                name='username',
                description='Enter your username.',
                type=OptionType.string,
                required=True
            ),
            Option(
                name='account_type',
                description='Select a default Account Type (optional.)',
                type=OptionType.string,
                required=False
            )
        ]
    )
    async def setrsn(
        self,
        inter: ApplicationCommandInteraction,
        username: str,
        account_type: str = None
    ) -> None:
        '''
        Creates a slash command for the `set_username` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param username: (String) -
            Represents a player's username.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)

        :return: (None)
        '''

        embed, view = await self.set_username(
            inter,
            username,
            account_type
        )
        await inter.send(embed=embed, view=view, ephemeral=True)


    @setrsn.autocomplete('account_type')
    async def account_type_autocomplete(self, account_type: str) -> List[str]:
        '''
        Creates a selection of autocomplete suggestions once the user begins
        typing.

        :param self: -
            Represents this object.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)

        :return: (List[String]) -
            A list of autocomplete suggestions.
        '''

        _ = account_type

        return ACCOUNT_TYPES


def setup(bot: Bot) -> None:
    '''
    Defines the bot setup function for the `setrsn` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Setrsn(bot))
