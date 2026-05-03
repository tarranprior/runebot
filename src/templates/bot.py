#! /usr/bin/env python3

'''
This module contains the `Bot` class logic for representing a
Discord bot instance, in the context of Runebot.

Functions:

    Coroutines:
        - `async def on_connect()`:
                A coroutine that is called when the bot has connected
                to the Discord gateway.
        - `async def on_ready()`:
                A coroutine that executes when the bot is fully
                initialised and ready to respond to events.
        - `async def on_guild_join()`:
                A coroutine that is called when the bot joins a guild.
        - `async def on_guild_remove()`:
                A coroutine that is called when the bot leaves a guild.
        - `async def on_slash_command_error()`:
                A coroutine that is called when a slash command
                encounters an error.
        - `@tasks.loop(minutes=10.0) async def status()`:
                A coroutine that updates the bot's status every 10
                minutes.

    Key Methods:
        - `__init__()`:
                Initialises a new instance of the Bot class.
        - `load_extensions()`:
                Loads all extensions (cogs) for the bot.

Each function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import platform
import os
import aiosqlite
import disnake
from datetime import datetime, timezone

from disnake.ext import commands, tasks
from disnake import ApplicationCommandInteraction
from loguru import logger

from config import *
from utils import (
    DISPLAY_VERSION,
    EmbedFactory,
    configuration,
    add_guild,
    remove_guild,
)
from utils.runtime_stats import get_community_stats


class Bot(commands.InteractionBot):
    '''
    A class which represents a Discord bot instance.
    '''

    def __init__(self, config=None, db_path=None, *args, **kwargs) -> None:
        '''
        Initialises a new instance of the Bot class.

        :param self: -
            Represents this object.
        :param config: (Optional[Dictionary]) -
            A dictionary containing configuration details.
        :param db_path: (String) -
            SQLite database path.

        :return: (None)
        '''

        super().__init__(*args, **kwargs)
        self.bot = Bot
        self.config = config or configuration()
        self.db_path = db_path
        self.runtime_started_at_utc = None


    def load_extensions(self, exts: list) -> None:
        '''
        Loads all extensions (cogs) for the bot.

        :param self: -
            Represents this object.
        :param exts: (List) -
            A list of file paths for the extensions.

        :return: (None)
        '''

        count = 0
        loaded_extensions = []
        failed_extensions = []

        for ext in exts:
            try:
                self.load_extension(ext)
                loaded_extensions.append(ext)
                count += 1
            except Exception as exc:
                exception = f'{type(exc).__name__}: {exc}'
                failed_extensions.append(
                    {
                        'extension': ext,
                        'exception': exception,
                    }
                )
                logger.error(
                    f'Unable to load extension: {ext}\n{exception}.'
                )

        logger.bind(
            loaded_extensions=loaded_extensions,
            failed_extensions=failed_extensions,
        ).info(f'{count} extension(s) have loaded successfully.\n')


    async def on_connect(self) -> None:
        '''
        A coroutine that is called when the bot has connected to
        the Discord gateway.

        :param self: -
            Represents this object.

        :return: (None)
        '''

        logger.success(f'Runebot ({DISPLAY_VERSION}) is connected to the gateway.')
        logger.info(f'Logged in as {self.user.name} ({self.user.id}.)')
        logger.info(f'API Version: {disnake.__version__}')
        logger.info(
            f'Platform: {platform.system()} '
            f'{platform.release()} {os.name}\n'
        )

        setattr(self.bot, 'runebotdb', await aiosqlite.connect(self.db_path))
        async with self.bot.runebotdb.cursor() as cursor:
            await cursor.execute('PRAGMA foreign_keys = ON;')
            await cursor.execute('PRAGMA journal_mode=WAL;')
            await cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS all_articles (
                    article_title TEXT NOT NULL,
                    article_category TEXT NOT NULL
                );
                '''
            )
            await cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS all_guilds (
                    guild_id INTEGER NOT NULL,
                    guild_owner_id INTEGER NOT NULL,
                    colour_mode BOOLEAN NOT NULL
                );
                '''
            )
            await cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS all_users (
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    default_account_id INTEGER NULL
                );
                '''
            )
            await cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT NOT NULL,
                    UNIQUE(user_id, username, account_type)
                );
                '''
            )
            await cursor.execute(
                '''
                CREATE INDEX IF NOT EXISTS idx_user_accounts_user_id
                ON user_accounts(user_id)
                '''
            )

        await self.bot.runebotdb.commit()


    async def on_ready(self) -> None:
        '''
        A coroutine that executes when the bot is fully initialised
        and ready to respond to events.

        :param self: -
            Represents this object.

        :return: (None)
        '''

        await self.wait_until_ready()
        if self.runtime_started_at_utc is None:
            self.runtime_started_at_utc = datetime.now(timezone.utc)

        stats = get_community_stats(self, self.runtime_started_at_utc)

        logger.success('Runebot is ready.')
        logger.info(f'Connected to {stats.users} users in {stats.servers} guild(s.)')
        logger.info(f'Speaking in {stats.channels} total channels.')
        logger.info('For more information on usage, see the README.\n\n')


    async def on_guild_join(self, guild) -> None:
        '''
        A coroutine that is called when the bot joins a guild.

        :param self: -
            Represents this object.
        :param guild: (Guild) -
            The guild the bot joined.

        :return: (None)
        '''

        await add_guild(self, guild.id, guild.owner_id, True)


    async def on_guild_remove(self, guild) -> None:
        '''
        A coroutine that is called when the bot leaves a guild.

        :param self: -
            Represents this object.
        :param guild: (Guild) -
            The guild the bot left.

        :return: (None)
        '''

        await remove_guild(self, guild.id)


    async def on_slash_command_error(
        self,
        inter: ApplicationCommandInteraction,
        error: Exception
    ) -> None:
        '''
        A coroutine that is called when a slash command encounters
        an error.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            The interaction that resulted in the error.
        :param error: (Exception) -
            The error that was raised.

        :return: (None)
        '''

        async def _send_error_response(embed, view, **kwargs):
            if inter.response.is_done():
                return await inter.followup.send(embed=embed, view=view, **kwargs)
            return await inter.response.send_message(embed=embed, view=view, **kwargs)

        if isinstance(error, commands.errors.CommandInvokeError):

            if 'Nonexistence' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = GRAYSCALE_THUMBNAILS['bucket'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view
                )

            elif 'NoAlchemyData' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = GRAYSCALE_THUMBNAILS['filler'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view
                )

            elif 'NoHiscoreData' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = THUMBNAILS['filler'],
                    colour=0xB72615,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

            elif 'NoMinigameData' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = GRAYSCALE_THUMBNAILS['filler'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view
                )

            elif 'NoMonsterData' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = GRAYSCALE_THUMBNAILS['filler'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view
                )

            elif 'NoPriceData' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = GRAYSCALE_THUMBNAILS['filler'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view
                )

            elif 'NoQuestData' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url=GRAYSCALE_THUMBNAILS['filler'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view
                )

            elif 'NoAdministratorPermissions' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='This command is for server administrators only.',
                    description=str(error.__cause__),
                    thumbnail_url = THUMBNAILS['filler'],
                    colour=0xB72615,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

            elif 'StubArticle' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='This project page is a stub.',
                    description=str(error.__cause__),
                    thumbnail_url=THUMBNAILS['stub'],
                    colour=0x60533E,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view
                )

            elif 'UsernameInvalid' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = THUMBNAILS['filler'],
                    colour=0xB72615,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

            elif 'UsernameNonexistent' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = GRAYSCALE_THUMBNAILS['filler'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

            elif 'MaximumAccountsReached' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = THUMBNAILS['filler'],
                    colour=0xB72615,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

            elif 'NoGameModeData' in str(error.__str__()):
                embed, view = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(error.__cause__),
                    thumbnail_url = GRAYSCALE_THUMBNAILS['filler'],
                    colour=0x8B8B8B,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                return await _send_error_response(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

        logger.error(
            f'Ignoring exception in slash command {inter.application_command.name}: {error}')


    @tasks.loop(minutes=10.0)
    async def status() -> None:
        '''
        A coroutine that updates the bot's status every 10 minutes.

        :return: (None)
        '''

        await Bot.change_presence(
            activity=disnake.Game(
                name=Bot.config['configuration']['activity']
            )
        )
