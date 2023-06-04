#! /usr/bin/env python3

'''
This module contains the main entry point for the bot. It performs the
following:

- Loads environmental variables using `dotenv`.
- Initializes the `Bot` object with the appropriate settings.
- Loads all the necessary extensions using `bot.load_extensions`.
- Runs the bot using the `BOT_TOKEN` environmental variable.

The `Bot` object is configured to use a custom `disnake.Game` object for
the bot's activity, as well as to use case-insensitive commands, no built-in
help command, and all available `Intents`. 

The `bot.load_extensions` method loads the following cogs:

    - `administrator.ping`
    - `player_utilities.setrsn`
    - `player_utilities.stats`
    - `player_utilities.unsetrsn`
    - `search_tools.alchemy`
    - `search_tools.bestiary`
    - `search_tools.minigames`
    - `search_tools.price`
    - `search_tools.quests`
    - `search_tools.wikipedia`

For more information about each cog and its usage, refer to the docstrings
in the corresponding `py` file.
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
        ),
        case_insensitive=True,
        help_command=None,
        intents=disnake.Intents.all())

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
