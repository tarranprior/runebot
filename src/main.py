#! /usr/bin/env python3

'''
This module contains the main entry point for the bot.
For more information about each cog and its usage, refer to the docstrings
in the respective module.
'''

from os import environ as env
from dotenv import load_dotenv

import disnake

from templates.bot import Bot
from utils.helpers import configuration

load_dotenv()

if __name__ == '__main__':

    bot = Bot(
        activity=disnake.Game(
            name=f"{configuration()['configuration']['activity']}"
        )
    )

    bot.load_extensions(exts=[
        'cogs.administrator.ping',
        'cogs.player_utilities.setrsn',
        'cogs.player_utilities.stats',
        'cogs.player_utilities.unsetrsn',
        'cogs.search_tools.alchemy',
        'cogs.search_tools.bestiary',
        'cogs.search_tools.minigames',
        'cogs.search_tools.price',
        'cogs.search_tools.quests',
        'cogs.search_tools.wikipedia'
    ])

bot.run(env['BOT_TOKEN'])
