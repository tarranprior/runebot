'''
Database function which adds a new guild to the 'all_guilds' table.
:param self:
:param guild_id: (Integer) - Represents the guild id.
:param guild_owner_id: (Integer) - Represents the guild owner id.
:param toggle: (Boolean) - Represents the colour mode toggle. (Default: True)
'''


async def add_guild(self, guild_id: int, guild_owner_id: int, toggle: bool) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('INSERT INTO all_guilds (guild_id, guild_owner_id, colour_mode) VALUES (?, ?, ?)', (guild_id, guild_owner_id, toggle,))
        return (await self.bot.runebotdb.commit())


'''
Database function which gets all articles from the `all_articles` table.
:param self:
'''


async def get_all_articles(self) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('SELECT article_title FROM all_articles')
        article_titles = [article[0] for article in await cursor.fetchall()]
        return (article_titles)


'''
Database function which gets all guilds from the `all_guilds` table.
:param self:
'''


async def get_all_guilds(self) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('SELECT guild_id FROM all_guilds')
        guild_ids = [str(guild_ids) for guild_ids in await cursor.fetchall()]
        return (guild_ids)


'''
Database function which returns all tradeable item autocomplete suggestions (similar to `get_wikipedia_suggestions` but only returns tradeable items.)
:param self:
:param categories: (List) - Represents a list of categories.
'''


async def get_suggestions(self, categories: list) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        autocomplete_suggestions = []
        for category in categories:
            await cursor.execute(f'SELECT article_title FROM all_articles WHERE article_category = ?', (category,))
            autocomplete_suggestions.append(list(str(article[0]) for article in await cursor.fetchall()))
        return ([li for each_list in autocomplete_suggestions for li in each_list])


'''
Database function which returns all autocomplete suggestions (similar to `get_all_articles` but removes clutter such as dates etc.)
:param self:
'''


async def get_wikipedia_suggestions(self) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('SELECT article_title FROM all_articles WHERE article_category != ?', ("Dates in RuneScape",))
        autocomplete_suggestions = [str(article[0]) for article in await cursor.fetchall()]
        return (autocomplete_suggestions)


'''
Database function which checks whether `colour_mode` is set to True/False with a given guild identifier.
:param self:
:param guild_id: (Integer) - Represents the guild id.
:param guild_owner_id: (Integer) - Represents the owner's id of the guild.
'''


async def get_colour_mode(self, guild_id: int, guild_owner_id: int) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        try:
            await cursor.execute('SELECT colour_mode FROM all_guilds WHERE guild_id = ?', (guild_id,))
            colour_mode = await cursor.fetchone()
            if colour_mode[0]:
                return (True)
            return (False)
        except TypeError:
            await add_guild(self, guild_id, guild_owner_id, True)
            return (True)


'''
Database function which removes a guild from the `all_guilds` table.
:param self:
:param guild_id: (Integer) - Represents the guild id.
'''


async def remove_guild(self, guild_id: int) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('DELETE FROM all_guilds WHERE guild_id = ?', (guild_id,))
        return (await self.bot.runebotdb.commit())


'''
Database function which toggles `colour_mode` for a given guild.
:param self:
:param guild_id: (Integer) - Represents the guild id.
:param toggle: (Boolean) - Represents the colour mode toggle.
'''


async def update_colour_mode(self, guild_id: int, toggle: bool) -> None:
    async with self.bot.runebotdb.cursor() as cursor:
        await cursor.execute('UPDATE all_guilds SET colour_mode = ? WHERE guild_id = ?', (toggle, guild_id,))
        return (await self.bot.runebotdb.commit())
