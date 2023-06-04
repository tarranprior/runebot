#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `unsetrsn`
command, allowing users to remove a RuneScape username from their
Discord account.

Classes:
    - `Unsetrsn`:
            A class for handling the `unsetrsn` command.

Key Functions:
    - `unset_username(...)`, `unsetrsn(...)`:
            Functions for removing a RuneScape username, as well as
            creating a slash command and autocomplete query for the `unsetrsn`
            command.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `unsetrsn` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from disnake.ext import commands
from disnake import ApplicationCommandInteraction

from templates.bot import Bot
from config import *
from utils import *


class Unsetrsn(commands.Cog, name='unsetrsn'):
    '''
    A class which represents the Unsetrsn cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises the Unsetrsn cog.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        return: (None)
        '''
        self.bot = bot


    async def unset_username(
        self,
        inter: ApplicationCommandInteraction
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        Function which takes a provided username and removes it
        from the Runebot database.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.

        :return: (Tuple[disnake.Embed, disnake.ui.View])
            An embed and view containing a success message.
        '''

        username, account_type = await get_username(self, inter.author.id)
        if not username:
            raise exceptions.UsernameNonexistent
        await remove_username(self, inter.author.id)

        embed = EmbedFactory().create(
            title=f'Username has been unset.',
            description=f'Your username has now been unset. '
            'You can set another username at any time by using `/setrsn`.'
        )
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'Runebot {VER}')

        return embed


    @commands.slash_command(
        name='unsetrsn',
        description='Unset a RuneScape username from your Discord account.',
    )
    async def unsetrsn(
        self,
        inter: ApplicationCommandInteraction,
    ) -> None:
        '''
        Creates a slash command for the `unset_username` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.

        :return: (None)
        '''

        embed = await self.unset_username(
            inter
        )
        await inter.send(embed=embed, ephemeral=True)


def setup(bot: Bot) -> None:
    '''
    Defines the bot setup function for the `unsetrsn` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Unsetrsn(bot))
