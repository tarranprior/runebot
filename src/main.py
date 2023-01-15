from templates.bot import Bot
from utils.helpers import configuration

import disnake

from dotenv import load_dotenv
from os import environ as env


load_dotenv()

if __name__ == '__main__':

    bot = Bot(
        activity=disnake.Game(
            name=f"{configuration()['configuration']['activity']}"),
        case_insensitive=True,
        help_command=None,
        intents=disnake.Intents.all())

bot.load_extensions(exts=[
    'cogs.administrator.ping',
    'cogs.administrator.purge',
    'cogs.administrator.toggle',
    'cogs.search_tools.alchemy',
    'cogs.search_tools.bestiary',
    'cogs.search_tools.minigames',
    'cogs.search_tools.price',
    'cogs.search_tools.quests',
    'cogs.search_tools.wikipedia'
])

bot.run(env['BOT_TOKEN'])
