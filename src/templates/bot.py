from config import *
from utils import *

import aiosqlite
import disnake
import platform
import os

from disnake.ext import commands, tasks
from disnake import ApplicationCommandInteraction
from loguru import logger


class Bot(commands.Bot):
    def __init__(self, config=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, command_prefix='/')
        self.bot = Bot
        self.config = config or configuration()

    def load_extensions(self, exts: list):
        count = 0
        for ext in exts:
            try:
                self.load_extension(ext)
                logger.success(ext)
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

        setattr(self.bot, 'runebotdb', await aiosqlite.connect('runebot.db'))
        async with self.bot.runebotdb.cursor() as cursor:
            await cursor.execute(
                f'''
                CREATE TABLE IF NOT EXISTS all_guilds (
                    guild_id INTEGER NOT NULL,
                    guild_owner_id INTEGER NOT NULL,
                    colour_mode BOOLEAN NOT NULL
                )
                '''
            )
            await cursor.execute(
                f'''
                CREATE TABLE IF NOT EXISTS all_articles (
                    article_title TEXT NOT NULL,
                    article_category TEXT NOT NULL
                )
                '''
            )

    async def on_ready(self) -> None:
        logger.success('Runebot is ready.')
        logger.info('For more information on usage, see the README.')

    async def on_guild_join(self, guild) -> None:
        await add_guild(self, guild.id, guild.owner_id, True)

    async def on_guild_remove(self, guild) -> None:
        await remove_guild(self, guild.id)

    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error) -> None:
        if isinstance(error, commands.errors.CommandInvokeError):

            if 'Nonexistence' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='Nothing interesting happens.', description=str(error.__cause__),
                                                    thumbnail_url=BUCKET_ICO, colour=0x7E6E4D, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'NoAlchemyData' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='Nothing interesting happens.', description=str(error.__cause__),
                                                    thumbnail_url=BUCKET_ICO, colour=0x7E6E4D, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'NoExamineText' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='Nothing interesting happens.', description=str(error.__cause__),
                                                    thumbnail_url=BUCKET_ICO, colour=0x7E6E4D, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'NoMinigameData' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='Nothing interesting happens.', description=str(error.__cause__),
                                                    thumbnail_url=BUCKET_ICO, colour=0x7E6E4D, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'NoMonsterData' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='Nothing interesting happens.', description=str(error.__cause__),
                                                    thumbnail_url=BUCKET_ICO, colour=0x7E6E4D, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'NoPriceData' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='Nothing interesting happens.', description=str(error.__cause__),
                                                    thumbnail_url=BUCKET_ICO, colour=0x7E6E4D, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'NoQuestData' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='Nothing interesting happens.', description=str(error.__cause__),
                                                    thumbnail_url=BUCKET_ICO, colour=0x7E6E4D, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'NoAdministratorPermissions' in str(error.__str__()):
                embed, view = EmbedFactory().create(title='This command is for server administrators only.', description=str(error.__cause__),
                                                    colour=disnake.Colour.red(), button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

            elif 'StubArticle' in str(error.__str__()):
                embed = EmbedFactory().create(title='This project page is a stub.', description=str(error.__cause__),
                                                    thumbnail_url=STUB_ICO, colour=0x60533E, button_label='Support Server', button_url='https://discord.gg/FWjNkNuTzv')
                return await inter.followup.send(embed=embed, view=view)

        logger.error(
            f'Ignoring exception in slash command {inter.application_command.name}: {error}')

    @tasks.loop(minutes=10.0)
    async def status() -> None:
        await Bot.change_presence(activity=disnake.Game(name=Bot.config['configuration']['activity']))
