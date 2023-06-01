#! /usr/bin/env python3

'''
This module contains database logic for managing data and interacting
with the SQLite Runebot database.


Functions:
    - `add_guild()`:
            Adds a new guild to the 'all_guilds' table.
    - `get_all_articles()`:
            Retrieves all articles from the `all_articles` table.
    - `get_all_guilds()`:
            Retrieves all guilds from the `all_guilds` table.
    - `get_suggestions()`:
            Returns all tradeable item autocomplete suggestions.
    - `get_wikipedia_suggestions()`:
            Returns all autocomplete suggestions.
    - `get_colour_mode()`:
            Checks whether `colour_mode` is set to True/False with a given guild
            identifier.
    - `remove_guild()`:
            Removes a guild from the `all_guilds` table.
    - `update_colour_mode()`:
            Toggles `colour_mode` for a given guild.

Each function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from typing import List


async def add_guild(
    self,
    guild_id: int,
    guild_owner_id: int,
    toggle: bool
) -> None:
    '''
    Database function which adds a new guild to the 'all_guilds' table.

    :param self: -
        Represents this object.
    :param guild_id: (Integer) -
        Represents the guild id.
    :param guild_owner_id: (Integer) -
        Represents the guild owner id.
    :param toggle: (Boolean) -
        Represents the colour mode toggle. (Default: True)

    :return: (None)
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            INSERT INTO all_guilds (
                guild_id,
                guild_owner_id,
                colour_mode
            )
            VALUES (?, ?, ?)
            ''',
            (guild_id, guild_owner_id, toggle,)
        )

        return await self.bot.runebotdb.commit()


async def get_all_articles(self) -> List[str]:
    '''
    Database function which retrieves all articles from the
    `all_articles` table.

    :param self: -
        Represents this object.

    :return: (List[String]) -
        A list of all article titles.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('SELECT article_title FROM all_articles')
        article_titles = [article[0] for article in await cursor.fetchall()]
        return article_titles


async def get_all_guilds(self) -> List[str]:
    '''
    Database function which retrieves all guilds from the
    `all_guilds` table.

    :param self: -
        Represents this object.

    :return: (List[String]) -
        A list of all guild IDs.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('SELECT guild_id FROM all_guilds')
        guild_ids = [str(guild_ids) for guild_ids in await cursor.fetchall()]
        return guild_ids


async def get_suggestions(self, categories: list) -> None:
    '''
    Database function which returns all tradeable item autocomplete suggestions
    (similar to `get_wikipedia_suggestions` but only returns tradeable items.)

    :param self: -
        Represents this object.
    :param categories: (List[String]) -
        Represents a list of categories.

    :return: (List[String]) -
        A flattened list of article suggestions.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        autocomplete_suggestions = []

        for category in categories:
            await cursor.execute(
                '''
                SELECT article_title FROM all_articles WHERE article_category = ?
                ''',
                (category,)
            )
            autocomplete_suggestions.append(
                list(str(article[0]) for article in await cursor.fetchall())
            )

        return [
            li for each_list in autocomplete_suggestions for li in each_list
        ]


async def get_wikipedia_suggestions(self) -> List[str]:
    '''
    Database function which returns all autocomplete suggestions
    (similar to `get_all_articles` but removes clutter such as dates etc.)

    :param self: -
        Represents this object.

    :return: (List[str]) -
        A list of article suggestions.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            SELECT article_title FROM all_articles WHERE article_category != ?
            ''',
            ("Dates in RuneScape",)
        )

        autocomplete_suggestions = [
            str(article[0]) for article in await cursor.fetchall()
        ]
        return autocomplete_suggestions


async def get_colour_mode(self, guild_id: int, guild_owner_id: int) -> bool:
    '''
    Database function which checks whether `colour_mode` is set to True/False
    with a given guild identifier.

    :param self: -
        Represents this object.
    :param guild_id: (Integer) -
        Represents the guild id.
    :param guild_owner_id: (Integer) -
        Represents the owner's id of the guild.

    :return: (Boolean) -
        The colour mode value for the specified guild.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        try:
            await cursor.execute(
                '''
                SELECT colour_mode FROM all_guilds WHERE guild_id = ?
                ''',
                (guild_id,)
            )

            colour_mode = await cursor.fetchone()
            if colour_mode[0]:
                return True
            return False

        except TypeError:
            await add_guild(self, guild_id, guild_owner_id, True)
            return True


async def remove_guild(self, guild_id: int) -> None:
    '''
    Database function which removes a guild from the `all_guilds` table.

    :param self: -
        Represents this object.
    :param guild_id: (Integer) -
        Represents the guild id.

    :return: (None)
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            DELETE FROM all_guilds WHERE guild_id = ?
            ''',
            (guild_id,)
        )

        return await self.bot.runebotdb.commit()


async def update_colour_mode(self, guild_id: int, toggle: bool) -> None:
    '''
    Database function which toggles `colour_mode` for a given guild.

    :param self: -
        Represents this object.
    :param guild_id: (Integer) -
        Represents the guild id.
    :param toggle: (Boolean) -
        Represents the colour mode toggle.

    :return: (None)
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            UPDATE all_guilds SET colour_mode = ? WHERE guild_id = ?
            ''',
            (toggle, guild_id,))

        return await self.bot.runebotdb.commit()
