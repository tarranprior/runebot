import os, platform
from loguru import logger

import disnake
from disnake.ext import commands, tasks
from disnake import ApplicationCommandInteraction

from utils import *

class Bot(commands.Bot):
    def __init__(self, config = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = config or load_configuration()
        self.bot = Bot

    def load_extensions(self, exts: list):
        count = 0
        for ext in exts:
            try:
                self.load_extension(ext)
                logger.success(f"Load ext: '{ext}' complete.")
                count += 1
            except Exception as e:
                exception = f'{type(e).__name__}: {e}'
                logger.error(f'Unable to load extension: {ext}\n{exception}.')

        logger.info(f'{count} extension(s) have loaded successfully.\n')

    async def on_connect(self) -> None:
        logger.success('Bot is connected to the gateway.')
        logger.info(f'Connected to {len(self.guilds)} guild(s.)')
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        logger.info(f'API Version: {disnake.__version__}')
        logger.info(f'Platform: {platform.system()} {platform.release()} {os.name}\n')

    async def on_ready(self) -> None:
        logger.success('Bot is ready.')
        logger.info('For more information on usage, see the README.')

    async def on_command_error(self, ctx: disnake.ext.commands.Context, error) -> None:
        if isinstance(error, commands.errors.CommandNotFound):
            return

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            embed = EmbedFactory().create(title='Missing Required Argument', description=f"{str(error).capitalize()}\nFor more information on usage and parameters, use `{load_configuration()['configuration']['prefix']}help <command>`.", colour=disnake.Colour.red())
            return await ctx.reply(embed=embed)

        elif isinstance(error, commands.errors.CommandInvokeError):
            if 'Nonexistence' in str(error.__str__()):
                embed = EmbedFactory().create(title='Nonexistence', description=str(error.__cause__), colour=disnake.Colour.red())
                return await ctx.reply(embed=embed)

            elif 'NoPriceData' in str(error.__str__()):
                embed = EmbedFactory().create(title='No Price Data', description=str(error.__cause__), colour=disnake.Colour.red())
                return await ctx.reply(embed=embed)

            elif 'NoAlchData' in str(error.__str__()):
                embed = EmbedFactory().create(title='No Alch Data', description=str(error.__cause__), colour=disnake.Colour.red())
                return await ctx.reply(embed=embed)

            elif 'NoExamineText' in str(error.__str__()):
                embed = EmbedFactory().create(title='No Examine Text', description=str(error.__cause__), colour=disnake.Colour.red())
                return await ctx.reply(embed=embed)

        logger.error(f'Ignoring exception in command {ctx.command}: {error}')

    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error) -> None:
        if isinstance(error, commands.errors.CommandInvokeError):
            if 'Nonexistence' in str(error.__str__()):
                embed = EmbedFactory().create(title='Nonexistence', description=str(error.__cause__), thumbnail_url='https://oldschool.runescape.wiki/images/thumb/Weird_gloop_detail.png/75px-Weird_gloop_detail.png?94769')
                return await inter.response.send_message(embed=embed)

            elif 'NoPriceData' in str(error.__str__()):
                embed = EmbedFactory().create(title='No Price Data', description=str(error.__cause__), thumbnail_url='https://oldschool.runescape.wiki/images/thumb/Potato_detail.png/120px-Potato_detail.png?18b75')
                return await inter.response.send_message(embed=embed)

            elif 'NoAlchData' in str(error.__str__()):
                embed = EmbedFactory().create(title='No Alch Data', description=str(error.__cause__), thumbnail_url='https://oldschool.runescape.wiki/images/thumb/Potato_detail.png/120px-Potato_detail.png?18b75')
                return await inter.response.send_message(embed=embed)

            elif 'NoExamineText' in str(error.__str__()):
                embed = EmbedFactory().create(title='No Examine Text', description=str(error.__cause__), thumbnail_url='https://oldschool.runescape.wiki/images/thumb/Potato_detail.png/120px-Potato_detail.png?18b75')
                return await inter.response.send_message(embed=embed)

        logger.error(f'Ignoring exception in slash command {inter.application_command.name}: {error}')

    @tasks.loop(minutes=10.0)
    async def status() -> None:
        await Bot.change_presence(activity=disnake.Game(name=Bot.config['configuration']['activity']))