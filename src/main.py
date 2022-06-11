from os import environ as env
from dotenv import load_dotenv

import disnake
from templates.bot import Bot
from utils.general import load_configuration

load_dotenv()

if __name__ == '__main__':

    bot = Bot(
        activity=disnake.Game(name=load_configuration()['configuration']['activity']),
        case_insensitive=True,
        command_prefix=load_configuration()['configuration']['prefix'],
        help_command=None,
        intents=disnake.Intents.all(),
        owner_id=int(env['BOT_OWNER'])
    )

bot.load_extensions(exts=[
    'cogs.alch',
    'cogs.developer',
    'cogs.examine',
    'cogs.price',
    'cogs.quests',
    'cogs.wiki'
])

bot.run(env['BOT_TOKEN'])