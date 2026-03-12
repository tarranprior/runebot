#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `stats`
command, allowing users to search for player stats from the official API.

Classes:
    - `Stats`:
            A class for handling the `stats` command.

Key Functions:
    - `search_hiscores(...)`, `stats(...)`, and
      `search_query_autocomplete(...)`:
            Functions for searching and retrieving Hiscore data, as well as
            creating a slash command and autocomplete query for the `stats`
            command.
    - `button_listener(...)`:
            Cog listener which listens for button events.
    - `callback(self, inter: disnake.MessageInteraction)`:
            A callback function for dropdown selection.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `stats` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *


class Stats(commands.Cog, name='stats'):
    '''
    A class which represents the Stats cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises the Stats cog.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        return: (None)
        '''
        self.bot = bot


    def _build_stats_view(
        self,
        hiscore_category: str,
        account_type: str,
        username: str,
        owner_id: int
    ) -> View:
        '''
        Builds the view with navigation and refresh buttons for /stats.

        :param self: -
            Represents this object.
        :param hiscore_category: (String) -
            Represents the active Hiscore category.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param username: (String) -
            Represents a player's username.
        :param owner_id: (Integer) -
            Represents the user ID who initiated the command.

        :return: (View) -
            A view containing stats navigation and refresh buttons.
        '''

        view = View(timeout=None)

        categories = {
            'skills': [
                ('Boss Kills', 'boss_kills'),
                ('Bounty Hunter', 'bounty_hunter'),
                ('Clue Scrolls', 'clue_scrolls')
            ],
            'boss_kills': [
                ('Skills', 'skills'),
                ('Bounty Hunter', 'bounty_hunter'),
                ('Clue Scrolls', 'clue_scrolls')
            ],
            'bounty_hunter': [
                ('Skills', 'skills'),
                ('Boss Kills', 'boss_kills'),
                ('Clue Scrolls', 'clue_scrolls')
            ],
            'clue_scrolls': [
                ('Skills', 'skills'),
                ('Boss Kills', 'boss_kills'),
                ('Bounty Hunter', 'bounty_hunter')
            ]
        }

        for label, category in categories.get(hiscore_category, []):
            view.add_item(
                disnake.ui.Button(
                    label=label,
                    style=disnake.ButtonStyle.grey,
                    custom_id=(
                        f'stats:navigate,{category},{account_type},'
                        f'{username},{owner_id}'
                    )
                )
            )

        view.add_item(
            disnake.ui.Button(
                label='⟳',
                style=disnake.ButtonStyle.secondary,
                custom_id=(
                    f'stats:refresh,{hiscore_category},{account_type},'
                    f'{username},{owner_id}'
                ),
                row=1
            )
        )

        return view


    async def search_hiscores(
        self,
        inter: ApplicationCommandInteraction | disnake.MessageInteraction,
        hiscore_category: str,
        account_type: str,
        username: str = None,
        owner_id: int = None
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        Function which takes a username and returns hiscore
        values from the official API in a structured format.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction | disnake.MessageInteraction) -
            Represents an interaction with an application command or component.
        :param hiscore_category: (String) -
            Represents the Hiscore category (Ex: Bosses, Skills etc.)
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param username: (String[Optional]) -
            Represents a player's username.
        :param owner_id: (Integer[Optional]) -
            Represents the user ID who initiated the command.

        :return: Tuple[disnake.Embed, disnake.ui.View] -
            An embed and view containing the hiscore information.
        '''

        if not username: # If a username wasn't provided...
            # Try to get a username from Runebot database.
            username, default_account_type = await get_username(self, inter.author.id)
            if username == None:
                raise exceptions.UsernameNonexistent
            if account_type == None:
                account_type = default_account_type

        # If the provided username is a Discord user...
        # Try to get a username from Runebot database.
        if username.startswith('<@') and username.endswith('>'):
            username, account_type = await get_username(
                self, username.replace('<@', '').replace('>', '')
            )
            if not username:
                raise exceptions.UsernameNonexistent

        if len(username) > MAX_CHARS or any(char in username for char in BLACKLIST_CHARS):
            raise exceptions.UsernameInvalid

        if not account_type:
            account_type = 'Normal'

        if owner_id == None:
            owner_id = inter.author.id

        if account_type == 'Normal':
            try:
                hiscore_data = parse_hiscores(
                    HISCORE_API_URLS.get(account_type),
                    HEADERS,
                    HISCORES_ORDER,
                    [username]
                )
            except IndexError as exc:
                raise exceptions.NoHiscoreData from exc

        else:
            try:
                hiscore_data = parse_hiscores(
                    HISCORE_API_URLS.get(account_type),
                    HEADERS,
                    HISCORES_ORDER,
                    [username]
                )
            except IndexError as exc1:
                try:
                    hiscore_data = parse_hiscores(
                        NORMAL_API,
                        HEADERS,
                        HISCORES_ORDER,
                        [username]
                    )
                except IndexError as exc2:
                    raise exceptions.NoHiscoreData from exc2
                raise exceptions.NoGameModeData from exc1

        emote = ACCOUNT_EMOTES.get(account_type, '')
        embed = EmbedFactory().create(
            title=f'Personal Hiscores',
            description=(
                f'Personal Hiscores for {emote} **{username}**\n\u200b\n'
            ),
        )

        if hiscore_category == 'skills':

            # Gets all combat levels of the player with the provided
            # Hiscore data.
            combat_levels = {}
            for skill in COMBAT_SKILLS:
                combat_levels.update(
                    {skill: int(hiscore_data.get(skill).split(',')[1])}
                )

            # Corrects Hitpoints level if the player has no experience.
            # (Replace Level 1 with Level 10.)
            hp_rank = hiscore_data.get('Hitpoints').split(',')[0]
            hp_level = hiscore_data.get('Hitpoints').split(',')[1]
            hp_experience = hiscore_data.get('Hitpoints').split(',')[2]
            if int(hp_level) < 10:
                hiscore_data.update(
                    {'Hitpoints':f'{hp_rank},{int(10)},{hp_experience}'}
                )
                combat_levels.update({'Hitpoints': int(10)})

            # Calculates combat level and experience of the player.
            combat_level = await calculate_combat_level(combat_levels)
            combat_experience = await calculate_combat_exp(COMBAT_SKILLS, hiscore_data)

            overall_level = f'{int(hiscore_data.get("Overall").split(",")[1]):,}'

            # Gets the overall rank of the player.
            overall_rank = f'{int(hiscore_data.get("Overall").split(",")[0]):,}'
            if overall_rank == '-1':
                overall_rank = '--'

            # Gets the overall experience of the player.
            overall_exp = f'{int(hiscore_data.get("Overall").split(",")[2]):,}'
            if overall_exp == '0':
                overall_exp = '--'

            for column_data in STAT_COLUMNS:
                column_text = "\n".join([
                    f"{SKILL_EMOTES.get(skill)} "
                    f"{hiscore_data.get(data).split(',')[1].replace('-1', '--')}"
                    for skill, data in column_data
                ]) + '\n\u200b\n'
                embed.add_field(name="\u200a", value=column_text, inline=True)

            embed.add_field(
                name=f'{SKILL_EMOTES.get("overall")} Overall',
                value=f'''
                    **Level**: {overall_level}
                    **XP**: {overall_exp}\n\u200b\n
                '''
            )

            embed.add_field(
                name=f'{SKILL_EMOTES.get("combat")} Combat',
                value=f'''
                    **Level**: {combat_level}
                    **XP**: {combat_experience}\n\u200b\n
                '''
            )

            view = self._build_stats_view(
                hiscore_category,
                account_type,
                username,
                owner_id
            )

        elif hiscore_category == 'boss_kills':

            for column_data in BOSS_COLUMNS:
                column_text = "\n".join([
                    f"{BOSS_EMOTES.get(boss)} {int(hiscore_data.get(data).split(',')[1]):,}"
                    if hiscore_data.get(data).split(',')[1] != '-1' 
                    else f"{BOSS_EMOTES.get(boss)} -"
                    for boss, data in column_data
                ]) + '\n\u200b\n'
                embed.add_field(name="\u200a", value=column_text, inline=True)

            view = self._build_stats_view(
                hiscore_category,
                account_type,
                username,
                owner_id
            )

        elif hiscore_category == 'bounty_hunter':

            for column_data in BOUNTY_COLUMNS:
                column_text = "\n".join([
                    f"{BOUNTY_EMOTES.get(bounty)} {int(hiscore_data.get(data).split(',')[1]):,}"
                    if hiscore_data.get(data).split(',')[1] != '-1' 
                    else f"{BOUNTY_EMOTES.get(bounty)} -"
                    for bounty, data in column_data
                ]) + '\n\u200b\n'
                embed.add_field(name="\u200a", value=column_text, inline=True)

            view = self._build_stats_view(
                hiscore_category,
                account_type,
                username,
                owner_id
            )

        elif hiscore_category == 'clue_scrolls':

            for column_data in CLUE_COLUMNS:
                column_text = "\n".join([
                    f"{CLUE_EMOTES.get(clue)} {int(hiscore_data.get(data).split(',')[1]):,}"
                    if hiscore_data.get(data).split(',')[1] != '-1' 
                    else f"{CLUE_EMOTES.get(clue)} -"
                    for clue, data in column_data
                ]) + '\n\u200b\n'
                embed.add_field(name="\u200a", value=column_text, inline=True)

            view = self._build_stats_view(
                hiscore_category,
                account_type,
                username,
                owner_id
            )

            cluescroll_rank, cluescroll_total = [
                '-' if (value := hiscore_data.get(
                    'Clue Scrolls (All)'
                ).split(',')[index].replace('-1', '-')) == '-'
                else f'{int(value):,}'
                for index in range(2)
            ]

            embed.add_field(
                name=f'{CLUE_EMOTES.get("cluescrolls_all")} Clue Scrolls (all)',
                value=f'''
                    **Count**: {cluescroll_total}
                    **Rank**: {cluescroll_rank}\n\u200b\n
                '''
            )

        embed.set_footer(
            text=(
                'Experience data from the official Hiscores API\n'
                f'Runebot {DISPLAY_VERSION}'
            )
        )
        embed.timestamp = inter.created_at
        return embed, view


    @commands.slash_command(
        name='stats',
        description='Fetch player stats from the official Hiscores.',
        options=[
            Option(
                name='username',
                description='Search for a Player.',
                type=OptionType.string,
                required=False
            ),
            Option(
                name='account_type',
                description='Select an Account Type (optional.)',
                type=OptionType.string,
                required=False
            )
        ]
    )
    async def stats(
        self,
        inter: ApplicationCommandInteraction,
        account_type: str = None,
        *,
        username: str = None
    ) -> None:
        '''
        Creates a slash command for the `search_hiscores` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param account_type: (String[Optional]) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param username: (String[Optional]) -
            Represents a player's username.

        :return: (None)
        '''

        hiscore_category = 'skills'
        embed, view = await self.search_hiscores(
            inter,
            hiscore_category,
            account_type,
            username,
            inter.author.id
        )
        await inter.response.send_message(
            embed=embed,
            view=view
        )


    @commands.Cog.listener('on_button_click')
    async def button_listener(
        self,
        inter: disnake.MessageInteraction
    ) -> None:
        '''
        Cog listener which handles button clicks for /stats navigation and refresh.

        :param self: -
            Represents this object.
        :param inter: (disnake.MessageInteraction) -
            Represents a message component interaction triggered by a stats button.

        :return: (None)
        '''
        custom_id = inter.component.custom_id

        if not custom_id or not custom_id.startswith('stats:'):
            return

        payload = custom_id.removeprefix('stats:')
        params = payload.split(',')

        if len(params) != 5:
            return

        action, hiscore_category, account_type, username, owner_id = params

        if action not in ['navigate', 'refresh']:
            return

        if str(inter.author.id) != owner_id:
            await inter.response.send_message(
                'Only the original author can use these buttons.',
                ephemeral=True
            )
            return

        loading_view = build_loading_button_view(inter)
        await inter.response.edit_message(view=loading_view)

        try:
            embed, view = await self.search_hiscores(
                inter,
                hiscore_category,
                account_type,
                username,
                int(owner_id)
            )
            await inter.edit_original_response(
                embed=embed,
                view=view
            )
        except Exception as exc:
            view = self._build_stats_view(
                hiscore_category,
                account_type,
                username,
                int(owner_id)
            )
            await inter.edit_original_response(view=view)
            raise exc


    @stats.autocomplete('account_type')
    async def account_type_autocomplete(self, account_type: str) -> List[str]:
        '''
        Creates a selection of autocomplete suggestions once the user begins
        typing.

        :param self: -
            Represents this object.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)

        :return: (List[String]) -
            A list of autocomplete suggestions.
        '''

        _ = account_type
        return ACCOUNT_TYPES


def setup(bot: Bot) -> None:
    '''
    Defines the bot setup function for the `stats` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Stats(bot))
