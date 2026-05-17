#! /usr/bin/env python3

'''
This module contains database logic for managing data and interacting
with the SQLite Runebot database.

Functions:
    - `add_guild()`:
            Adds a new guild to the 'all_guilds' table.
    - `add_username()`:
            Adds a new username to the 'all_users' table.
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
    - `remove_username()`:
            Removes a username from the `all_users` table.
        - `remove_user_account()`:
            Removes a specific saved account for a user.
    - `update_colour_mode()`:
            Toggles `colour_mode` for a given guild.

Each function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from typing import List, Optional, Tuple
from .models import DefaultAccount

import exceptions

from .helpers import utc_now_iso


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


async def add_username(
    self,
    user_id: int,
    username: str,
    account_type: str
) -> None:
    '''
    Database function which adds a new user/account and updates the
    user's default account.

    :param self: -
        Represents this object.
    :param user_id: (Integer) -
        Represents a user id.
    :param username: (String) -
        Represents a player's username.
    :param account_type: (String) -
        Represents an account type.

    :return: (None)
    '''

    username = username.strip()
    if not username:
        return

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            SELECT 1
            FROM all_users
            WHERE user_id = ?
            LIMIT 1
            ''',
            (user_id,)
        )
        existing_user = await cursor.fetchone()

        if not existing_user:
            await cursor.execute(
                '''
                INSERT INTO all_users (
                    user_id,
                    username,
                    account_type,
                    default_account_id
                )
                VALUES (?, ?, ?, NULL)
                ''',
                (user_id, username, account_type)
            )

        await cursor.execute(
            '''
            SELECT id, username
            FROM user_accounts
            WHERE user_id = ?
              AND LOWER(username) = LOWER(?)
              AND account_type = ?
            LIMIT 1
            ''',
            (user_id, username, account_type)
        )
        existing_account = await cursor.fetchone()

        timestamp = utc_now_iso()

        if existing_account:
            account_id = existing_account[0]

            await cursor.execute(
                '''
                UPDATE user_accounts
                SET last_used_at = ?
                WHERE id = ?
                ''',
                (timestamp, account_id)
            )
        else:
            await cursor.execute(
                '''
                SELECT COUNT(*)
                FROM user_accounts
                WHERE user_id = ?
                ''',
                (user_id,)
            )
            count_row = await cursor.fetchone()
            if count_row and count_row[0] >= 5:
                raise exceptions.MaximumAccountsReached

            await cursor.execute(
                '''
                INSERT INTO user_accounts (
                    user_id,
                    username,
                    account_type,
                    created_at,
                    last_used_at
                )
                VALUES (?, ?, ?, ?, ?)
                ''',
                (user_id, username, account_type, timestamp, timestamp)
            )

            await cursor.execute(
                '''
                SELECT id
                FROM user_accounts
                WHERE user_id = ?
                  AND username = ?
                  AND account_type = ?
                LIMIT 1
                ''',
                (user_id, username, account_type)
            )
            account = await cursor.fetchone()
            account_id = account[0] if account else None

        if account_id:
            await cursor.execute(
                '''
                SELECT username
                FROM user_accounts
                WHERE id = ?
                LIMIT 1
                ''',
                (account_id,)
            )
            account_row = await cursor.fetchone()
            stored_username = account_row[0] if account_row else username

            await cursor.execute(
                '''
                UPDATE all_users
                SET default_account_id = ?, username = ?, account_type = ?
                WHERE user_id = ?
                ''',
                (account_id, stored_username, account_type, user_id)
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
        guild_ids = [str(guild_id[0]) for guild_id in await cursor.fetchall()]
        return guild_ids


async def get_suggestions(self, categories: list) -> List[str]:
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


async def get_default_account(self, user_id: int) -> Optional[DefaultAccount]:
    '''
    Database function which retrieves a user's default account.

    :param self: -
        Represents this object.
    :param user_id: (Integer) -
        Represents a user id.

    :return: (Optional[DefaultAccount]) -
        The default account as a DefaultAccount dataclass, otherwise None.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        try:
            await cursor.execute(
                '''
                SELECT username, account_type, default_account_id
                FROM all_users
                WHERE user_id = ?
                LIMIT 1
                ''',
                (user_id,)
            )
            user_row = await cursor.fetchone()
        except Exception:
            # Defensive fallback for older/partial schemas.
            await cursor.execute(
                '''
                SELECT username, account_type
                FROM all_users
                WHERE user_id = ?
                LIMIT 1
                ''',
                (user_id,)
            )
            legacy_account = await cursor.fetchone()
            if not legacy_account:
                return None

            username, account_type = legacy_account

            await cursor.execute(
                '''
                SELECT id, username, account_type
                FROM user_accounts
                WHERE user_id = ? AND username = ? AND account_type = ?
                LIMIT 1
                ''',
                (user_id, username, account_type)
            )
            mapped_account = await cursor.fetchone()
            if mapped_account:
                return DefaultAccount(account_id=mapped_account[0], username=mapped_account[1], account_type=mapped_account[2])

            return None

        if not user_row:
            return None

        username, account_type, default_account_id = user_row

        if default_account_id:
            await cursor.execute(
                '''
                SELECT id, username, account_type
                FROM user_accounts
                WHERE id = ? AND user_id = ?
                LIMIT 1
                '''
                , (default_account_id, user_id)
            )
            account = await cursor.fetchone()
            if account:
                return DefaultAccount(account_id=account[0], username=account[1], account_type=account[2])

        await cursor.execute(
            '''
            SELECT id, username, account_type
            FROM user_accounts
            WHERE user_id = ? AND username = ? AND account_type = ?
            LIMIT 1
            '''
            , (user_id, username, account_type)
        )
        mapped_account = await cursor.fetchone()
        if mapped_account:
            return DefaultAccount(account_id=mapped_account[0], username=mapped_account[1], account_type=mapped_account[2])

        return None


async def get_username(self, user_id: int) -> Tuple[Optional[str], Optional[str]]:
    '''
    Database function which retrieves a username with a given user_id.

    :param self: -
        Represents this object.
    :param user_id: (Integer) -
        Represents a user id.

    :return: (Optional[String]) -
        The respective username of the Discord user_id.
    '''
    account = await get_default_account(self, user_id)
    if account:
        username = account.username
        account_type = account.account_type
        return username, account_type

    return None, None


async def get_user_accounts(self, user_id: int) -> List[Tuple[int, str, str]]:
    '''
    Database function which retrieves all accounts for a given user.

    :param self: -
        Represents this object.
    :param user_id: (Integer) -
        Represents a user id.

    :return: (List[Tuple[Integer, String, String]]) -
        A list of account rows in the form (id, username, account_type).
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            SELECT id, username, account_type
            FROM user_accounts
            WHERE user_id = ?
            ORDER BY last_used_at DESC, id ASC
            ''',
            (user_id,)
        )
        return await cursor.fetchall()


async def set_default_account(self, user_id: int, account_id: int) -> bool:
    '''
    Database function which sets a default account for a given user.

    :param self: -
        Represents this object.
    :param user_id: (Integer) -
        Represents a user id.
    :param account_id: (Integer) -
        Represents an account id.

    :return: (Boolean) -
        True if default account is updated, otherwise False.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            SELECT username, account_type
            FROM user_accounts
            WHERE id = ? AND user_id = ?
            LIMIT 1
            ''',
            (account_id, user_id)
        )
        account = await cursor.fetchone()
        if not account:
            return False

        username, account_type = account

        await cursor.execute(
            '''
            SELECT 1 FROM all_users WHERE user_id = ? LIMIT 1
            ''',
            (user_id,)
        )
        existing_user = await cursor.fetchone()

        if not existing_user:
            await cursor.execute(
                '''
                INSERT INTO all_users (
                    user_id,
                    username,
                    account_type,
                    default_account_id
                )
                VALUES (?, ?, ?, ?)
                ''',
                (user_id, username, account_type, account_id)
            )

        await cursor.execute(
            '''
            UPDATE all_users
            SET default_account_id = ?, username = ?, account_type = ?
            WHERE user_id = ?
            ''',
            (account_id, username, account_type, user_id)
        )

        await cursor.execute(
            '''
            UPDATE user_accounts
            SET last_used_at = ?
            WHERE id = ? AND user_id = ?
            ''',
            (utc_now_iso(), account_id, user_id)
        )

        await self.bot.runebotdb.commit()
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


async def remove_username(self, user_id: int):
    '''
    Database function which removes a username from the database.

    :param self: -
        Represents this object.
    :param user_id: (Integer) -
        Represents a user id.

    :return: (None)
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            DELETE FROM user_accounts WHERE user_id = ?
            ''',
            (user_id,)
        )

        await cursor.execute(
            '''
            DELETE FROM all_users WHERE user_id = ?
            ''',
            (user_id,)
        )

        return await self.bot.runebotdb.commit()


async def remove_user_account(self, user_id: int, account_id: int) -> bool:
    '''
    Database function which removes a specific account for a user and
    reassigns their default account where needed.

    :param self: -
        Represents this object.
    :param user_id: (Integer) -
        Represents a user id.
    :param account_id: (Integer) -
        Represents the account id to remove.

    :return: (Boolean) -
        True if an account was deleted, otherwise False.
    '''

    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute(
            '''
            SELECT 1
            FROM user_accounts
            WHERE user_id = ? AND id = ?
            LIMIT 1
            ''',
            (user_id, account_id)
        )
        account_exists = await cursor.fetchone()

        if not account_exists:
            return False

        await cursor.execute(
            '''
            DELETE FROM user_accounts
            WHERE user_id = ? AND id = ?
            ''',
            (user_id, account_id)
        )

        await cursor.execute(
            '''
            SELECT id, username, account_type
            FROM user_accounts
            WHERE user_id = ?
            ORDER BY last_used_at DESC, id ASC
            LIMIT 1
            ''',
            (user_id,)
        )
        next_default = await cursor.fetchone()

        if next_default:
            next_id, next_username, next_account_type = next_default

            await cursor.execute(
                '''
                SELECT 1 FROM all_users WHERE user_id = ? LIMIT 1
                ''',
                (user_id,)
            )
            existing_user = await cursor.fetchone()

            if existing_user:
                await cursor.execute(
                    '''
                    UPDATE all_users
                    SET default_account_id = ?, username = ?, account_type = ?
                    WHERE user_id = ?
                    ''',
                    (next_id, next_username, next_account_type, user_id)
                )
            else:
                await cursor.execute(
                    '''
                    INSERT INTO all_users (
                        user_id,
                        username,
                        account_type,
                        default_account_id
                    )
                    VALUES (?, ?, ?, ?)
                    ''',
                    (user_id, next_username, next_account_type, next_id)
                )
        else:
            await cursor.execute(
                '''
                DELETE FROM all_users WHERE user_id = ?
                ''',
                (user_id,)
            )

        await self.bot.runebotdb.commit()
        return True


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
