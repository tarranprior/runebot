import os, platform
from loguru import logger

import disnake
from disnake.ext import commands, tasks
from disnake import ApplicationCommandInteraction

from config import *
from utils import *


class Bot(commands.Bot):
    def __init__(self, config=None, base_url=None, headers=None, *args, **kwargs) -> None:
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
        logger.success('Runebot is connected to the gateway.')
        logger.info(f'Connected to {len(self.guilds)} guild(s.)')
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        logger.info(f'API Version: {disnake.__version__}')
        logger.info(f'Platform: {platform.system()} {platform.release()} {os.name}\n')

    async def on_ready(self) -> None:
        logger.success('Runebot is ready.')
        logger.info('For more information on usage, see the README.')

    async def on_command_error(self, ctx: disnake.ext.commands.Context, error) -> None:
        if isinstance(error, commands.errors.CommandNotFound):
            return

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            embed = EmbedFactory().create(
                                    title='Missing required argument',
                                    description=f"{str(error).capitalize()}\nFor more information on usage and parameters, use `{load_configuration()['configuration']['prefix']}help <command>`.",
                                    thumbnail_url=BUCKET_ICO
            )
            return await ctx.reply(embed=embed)

        elif isinstance(error, commands.errors.CommandInvokeError):
            
            if 'Nonexistence' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='Nonexistence',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await ctx.reply(embed=embed)

            elif 'NoAlchData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No alch data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await ctx.reply(embed=embed)

            elif 'NoExamineText' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No examine text',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await ctx.reply(embed=embed)
            
            elif 'NoMinigameData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No minigame data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await ctx.reply(embed=embed)

            elif 'NoMonsterData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No monster data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await ctx.reply(embed=embed)

            elif 'NoPriceData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No price data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await ctx.reply(embed=embed)
            
            elif 'NoQuestData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No quest data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await ctx.reply(embed=embed)

        logger.error(f'Ignoring exception in command {ctx.command}: {error}')

    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error) -> None:
        if isinstance(error, commands.errors.CommandInvokeError):
            
            if 'Nonexistence' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='Nonexistence',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await inter.response.send_message(embed=embed)

            elif 'NoAlchData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No alch data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await inter.response.send_message(embed=embed)

            elif 'NoExamineText' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No examine text',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await inter.response.send_message(embed=embed)

            elif 'NoMinigameData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No minigame data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await inter.response.send_message(embed=embed)

            elif 'NoMonsterData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No monster data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await inter.response.send_message(embed=embed)

            elif 'NoPriceData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No price data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await inter.response.send_message(embed=embed)
            
            elif 'NoQuestData' in str(error.__str__()):
                embed = EmbedFactory().create(
                                        title='No quest data',
                                        description=str(error.__cause__),
                                        thumbnail_url=BUCKET_ICO
                )
                return await inter.response.send_message(embed=embed)

        logger.error(f'Ignoring exception in slash command {inter.application_command.name}: {error}')

    @tasks.loop(minutes=10.0)
    async def status() -> None:
        await Bot.change_presence(activity=disnake.Game(name=Bot.config['configuration']['activity']))