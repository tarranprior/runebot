#! /usr/bin/env python3

'''
This module contains a `ping` command that allows users to view the
bot's current latency.

The `ping` command displays two latency values: `WS` for WebSocket, and
`REST` for REST API. The `WS` value measures the latency of the WebSocket
connection between the bot and Discord's servers, while the `REST` value
measures the latency of the REST API requests made by the bot to
Discord's servers.

Classes:
    - `Ping`:
            A class for handling the `ping` command.

Key Functions:
    - `calculate_ping(...)`:
            Calculates the bot's latency.
    - `ping(...)`:
            A slash command that calls the `calculate_ping` function.
    - `setup(bot: Bot)`:
            Defines the bot setup function for the `ping` command.

Note:
    This command can only be run by the server owner.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from config import *
from templates.bot import Bot
from utils import *

import time

from disnake.ext import commands
from disnake import ApplicationCommandInteraction


class Ping(commands.Cog, name='ping'):
    '''
    A class which represents the Ping cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Ping class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot


    async def calculate_ping(
        self,
        inter: ApplicationCommandInteraction
    ) -> None:
        '''
        A function for calculating the bot's latency.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.

        :return: (None)
        '''
        # Raise an error if the user does not have administritive
        # permissions.
        if not inter.user.id == inter.guild.owner_id:
            raise exceptions.NoAdministratorPermissions

        time_before = time.monotonic()

        embed, view = EmbedFactory().create(
            title='Pong!',
            description=(
                'Display the bot\'s latency.\n\nBot running slow? '
                'Contact the developer on '
                '[GitHub](https://github.com/tarranprior/runebot), '
                'or hit the button below.'
            ),
            button_label='Support Server',
            button_url=SUPPORT_SERVER
        )

        embed.add_field(
            name='Latency output',
            value=f'```\nPong! {round(self.bot.latency*1000)}ms • REST: ...```'
        )

        embed.timestamp = inter.created_at
        await inter.followup.send(embed=embed, view=view)

        rest = round((time.monotonic() - time_before) * 1000, 1)

        embed, view = EmbedFactory().create(
            title='Pong!',
            description=(
                'Display the bot\'s latency.\n\nBot running slow? '
                'Contact the developer on '
                '[GitHub](https://github.com/tarranprior/runebot), '
                'or hit the button below.'
            ),
            button_label='Support Server',
            button_url=SUPPORT_SERVER
        )

        embed.add_field(
            name='Latency output',
            value=(
                f'```WS: {round(self.bot.latency*1000, 1)}ms '
                f'• REST: {rest}ms```'
            )
        )

        embed.timestamp = inter.created_at
        embed.set_footer(text=f'Runebot {VER}')
        await inter.edit_original_message(embed=embed, view=view)


    @commands.slash_command(
        name='ping',
        description='Allows you to view the bot\'s current latency.'
    )
    async def ping(self, inter: ApplicationCommandInteraction) -> None:
        '''
        Creates a slash command for the `ping` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.

        :return: (None)
        '''
        await inter.response.defer()
        await self.calculate_ping(inter)


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `ping` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Ping(bot))
