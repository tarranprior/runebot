#! /usr/bin/env python3

'''
This module contains the main entry point for the bot.
For more information about each cog and its usage, refer to the docstrings
in the respective module.
'''

from os import environ as env
from dotenv import load_dotenv
from loguru import logger

import disnake

from templates.bot import Bot
from utils.helpers import configuration
from utils.internal_api import InternalStatsAPIServer

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

    api_token = env.get('RUNEBOT_INTERNAL_API_TOKEN', '')
    api_host = env.get('RUNEBOT_INTERNAL_API_HOST', '127.0.0.1')
    api_port_raw = env.get('RUNEBOT_INTERNAL_API_PORT', '8080')

    try:
        api_port = int(api_port_raw)
        if api_port < 1 or api_port > 65535:
            raise ValueError
    except ValueError:
        logger.warning(
            'Invalid RUNEBOT_INTERNAL_API_PORT value. Falling back to 8080.'
        )
        api_port = 8080

    internal_api = InternalStatsAPIServer(
        bot=bot,
        token=api_token,
        host=api_host,
        port=api_port
    )
    internal_api.start()

    bot.run(env['BOT_TOKEN'])
