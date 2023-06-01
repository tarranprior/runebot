#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `stats`
command, allowing users to search for player stats from the official API.

Classes:
    - `Stats`:
            A class for handling the `stats` command.
    - `Dropdown`:
            A class for creating dropdown options that can be added
            to a `DropdownView` instance.
    - `DropdownView`:
            A view class for creating dropdowns in the response.

Key Functions:
    - `search_hiscores(...)`, `stats(...)`, and
      `search_query_autocomplete(...)`:
            Functions for searching and retrieving Hiscore data, as well as
            creating a slash command and autocomplete query for the `stats`
            command.
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


    async def search_hiscores(
        self,
        inter: ApplicationCommandInteraction,
        hiscore_category: str,
        account_type: str,
        ephemeral: bool,
        xp: bool,
        username: str
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        General function which takes a username and returns hiscore
        values from the official API in a structured format.

        :param self: -
            Represents this object.
        :param hiscore_category: (String) -
            Represents the Hiscore category (Ex: Bosses, Skills etc.)
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param ephemeral: (Boolean) -
            Represents the ephemeral value. Defaults to False.
        :param xp: (Boolean) -
            Represents the xp value. Defaults to False.
        :param username: (String) -
            Represents a player's username.

        :return: Tuple[disnake.Embed, disnake.ui.View] -
            An embed and view containing the hiscore information.
        '''

        # Data validation which throws an error if the length of a username
        # exceeds 12 characters (max limit.)
        if len(username) > 12:
            raise exceptions.UsernameInvalid

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

        embed = EmbedFactory().create(
            title=f'Personal Hiscores',
            description=(
                f'Personal Hiscores for **{username}**\n'
                f'Account Type: `{account_type}`\n\u200b\n'
            ),
        )

        if hiscore_category == 'Skills':

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

            # Gets the overall rank of the player.
            overall_rank = f'{int(hiscore_data.get("Overall").split(",")[0]):,}'
            if overall_rank == '-1':
                overall_rank = 'N/A'

            # Gets the overall experience of the player.
            overall_exp = f'{int(hiscore_data.get("Overall").split(",")[2]):,}'
            if overall_exp == '0':
                overall_exp = 'N/A'

            for column_data in STAT_COLUMNS:
                column_text = "\n".join([
                    f"{SKILL_EMOTES.get(skill)} "
                    f"{hiscore_data.get(data).split(',')[1].replace('-1', '-')}"
                    + (f"\n{hiscore_data.get(data).split(',')[2].replace('-1', '-')}" if xp else "")
                    for skill, data in column_data
                ]) + '\n\u200b\n'
                embed.add_field(name="\u200a", value=column_text, inline=True)

            embed.add_field(
                name=f'{SKILL_EMOTES.get("overall")} Overall',
                value=f'''
                    **Rank**: {overall_rank}
                    **XP**: {overall_exp}
                '''
            )

            embed.add_field(
                name=f'{SKILL_EMOTES.get("combat")} Combat',
                value=f'''
                    **Level**: {combat_level}
                    **XP**: {combat_experience}
                '''
            )

            view = DropdownView(
                inter,
                ["Bosses"],
                account_type,
                ephemeral,
                xp,
                username
            )

        elif hiscore_category == 'Bosses':

            for column_data in BOSS_COLUMNS:
                column_text = "\n".join([
                    f"{BOSS_EMOTES.get(boss)} "
                    f"{hiscore_data.get(data).split(',')[1].replace('-1', '-')}"
                    for boss, data in column_data
                ]) + '\n\u200b\n'
                embed.add_field(name="\u200a", value=column_text, inline=True)

            view = DropdownView(
                inter,
                ["Skills"],
                account_type,
                ephemeral,
                xp,
                username
            )

        view.add_item(Button(
            label='Visit Hiscores',
            url=f'{HISCORE_URLS.get(account_type)}{slugify(username)}'
        ))

        embed.set_footer(
            text=(
                'Experience data from the official Hiscores API.\n'
                f'Runebot {VER}'
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
                required=True
            ),
            Option(
                name='account_type',
                description='Select an Account Type.',
                type=OptionType.string,
                required=False
            ),
            Option(
                name='xp',
                description='Toggle if you\'d like to display total xp for each skill.',
                type=OptionType.boolean,
                required=False
            ),
            Option(
                name='ephemeral',
                description='Toggle if you\'d like the response to be hidden to others.',
                type=OptionType.boolean,
                required=False
            )
        ]
    )
    async def stats(
        self,
        inter: ApplicationCommandInteraction,
        account_type: str = 'Normal',
        ephemeral: bool = False,
        xp: bool = False,
        *,
        username: str
    ) -> None:
        '''
        Creates a slash command for the `search_hiscores` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param account_type: (String[Optional]) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param ephemeral: (Boolean) -
            Represents the ephemeral value. Defaults to False.
        :param xp: (Boolean) -
            Represents the xp value. Defaults to False.
        :param username: (String) -
            Represents a player's username.

        :return: (None)
        '''

        embed, view = await self.search_hiscores(
            inter,
            'Skills',
            account_type,
            ephemeral,
            xp,
            username
        )
        await inter.send(
            embed=embed,
            view=view,
            ephemeral=ephemeral
        )


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
        return [
            'Ironman',
            'Hardcore Ironman',
            'Ultimate Ironman',
            'Skiller',
            '1 Defence',
            'Fresh Start Worlds'
        ]


class Dropdown(disnake.ui.StringSelect):
    '''
    A class which contains logic for the dropdown options (Select Menu.)
    '''

    def __init__(
        self,
        inter: ApplicationCommandInteraction,
        options: list,
        account_type: str,
        ephemeral: bool,
        xp: bool,
        username: str
    ) -> None:
        '''
        Initialises the Dropdown object.

        :param self: -
            Represents this object.
        :param options: (List) -
            Represents a list of strings representing the dropdown options.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param ephemeral: (Boolean) -
            Represents the ephemeral value.
        :param xp: (Boolean) -
            Represents the xp value. Defaults to False.
        :param username: (String) -
            Represents a player's username.

        :return: (None)
        '''

        self.bot = Bot
        self.inter = inter
        self.account_type = account_type
        self.ephemeral = ephemeral
        self.xp = xp
        self.username = username

        super().__init__(
            placeholder='Select another category.',
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        '''
        The callback function for dropdown selection (Select Menu.)

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.

        :return: (None)
        '''

        await inter.response.defer()
        embed, view = await Stats.search_hiscores(
            self,
            self.inter,
            self.values[0],
            self.account_type,
            self.ephemeral,
            self.xp,
            self.username
        )
        await inter.followup.send(
            embed=embed,
            view=view,
            ephemeral=self.ephemeral
        )


class DropdownView(disnake.ui.View):
    '''
    A class which contains logic for displaying a dropdown view.
    '''

    def __init__(
        self,
        inter: ApplicationCommandInteraction,
        options: list,
        account_type: str,
        ephemeral: bool,
        xp: bool,
        username: str,
        timeout=None
    ) -> None:
        '''
        :param self: -
            Represents this object.
        :param options: (List) -
            Represents a list of strings representing the dropdown options.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param username: (String) -
            Represents a player's username.
        :param ephemeral: (Boolean) -
            Represents the ephemeral value.
        :param xp: (Boolean) -
            Represents the xp value. Defaults to False.
        :param timeout: Optional([Integer]) -
            Represents the amount of time that the view remains active before
            timing out.

        :return: (None)
        '''

        self.bot = Bot
        super().__init__(timeout=timeout)
        self.add_item(Dropdown(
            inter, options, account_type, ephemeral, xp, username
        ))


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `stats` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Stats(bot))
