#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `stats`
command, allowing users to search for player stats from the official API.

Classes:
    - `Stats`:
            A class for handling the `stats` command.

Key Functions:
    - `search_hiscores(...)`, `stats(...)`, and
      `account_type_autocomplete(...)`:
            Functions for resolving usernames, retrieving Hiscore data, and
            defining the slash command and account type autocomplete for the
            `stats` command.
    - `button_listener(...)`:
            Cog listener which listens for button events.
    - `callback(self, inter: MessageInteraction)`:
            A callback function for dropdown selection.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `stats` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import asyncio
import time
import uuid
from disnake.ext import commands
from disnake import ApplicationCommandInteraction, MessageInteraction, Option, OptionType

import exceptions
from templates.bot import Bot
from config import *
from utils import *
from utils.logging import (
    BoundCommandLogger,
    build_command_log_bind,
    LogParam,
    serialize_params,
    serialize_resolved_username,
    build_stats_resolution_params,
    build_stats_failure_params,
    build_log_message,
    elapsed_ms,
)


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

        :return: (None)
        '''
        self.bot = bot
        self._stats_log = BoundCommandLogger(self._stats_bind)
    

    def _stats_bind(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        *,
        invocation_source: str,
        action: str = None,
        stage: str = None,
        operation: str = None,
        hiscore_category: str = None,
        account_type: str = None,
        username: str = None,
        resolved_username: str = None,
        resolved_account_type: str = None,
        resolution_source: str = None,
        trace_id: str | None = None,
        owner_id: int | str = None,
        log_params: list[dict] = None,
        **extra,
    ) -> dict:
        normalized_owner_id = str(owner_id) if owner_id is not None else None
        return build_command_log_bind(
            command='stats',
            inter=inter,
            action=action,
            stage=stage,
            operation=operation,
            invocation_source=invocation_source,
            trace_id=trace_id,
            resolution_source=resolution_source,
            log_params=log_params,
            hiscore_category=hiscore_category,
            account_type=account_type,
            username=username,
            resolved_username=resolved_username,
            resolved_account_type=resolved_account_type,
            owner_id=normalized_owner_id,
            **extra,
        )
    

    @staticmethod
    def _invocation_source(
        inter: ApplicationCommandInteraction | MessageInteraction
    ) -> str:
        return (
            'component_callback'
            if isinstance(inter, MessageInteraction)
            else 'slash_command'
        )


    async def _ack_invalid_stats_component(
        self,
        inter: MessageInteraction,
        trace_id: str,
        started_at: float,
    ) -> None:
        await ack_component_failure(
            inter,
            self._stats_log,
            'stats',
            description=f'This stats control is no longer valid. Please run {SLASH_MENTIONS["stats"]} again.',
            operation='invalid_component',
            invocation_source=self._invocation_source(inter),
            trace_id=trace_id,
            started_at=started_at,
        )


    def _log_component_start(
        self,
        inter: MessageInteraction,
        trace_id: str,
        operation: str,
        **metadata,
    ) -> None:
        self._stats_log.info(
            inter,
            build_log_message(command='stats', stage='start', operation=operation),
            trace_id=trace_id,
            invocation_source='component_callback',
            action='start',
            stage='start',
            operation=operation,
            **metadata,
        )


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

        view.add_item(
            disnake.ui.Button(
                label='Account Manager (Beta)',
                style=disnake.ButtonStyle.secondary,
                emoji=disnake.PartialEmoji(name='account', id=1482896847239381065),
                custom_id=f'stats:account_manager,{owner_id}',
                row=1
            )
        )

        return view


    def _build_account_manager_view(
        self,
        accounts: List[Tuple[int, str, str]],
        default_account,
        owner_id: int
    ) -> View:
        '''
        Builds the view containing the account select menu for the
        Account Manager ephemeral response.

        :param self: -
            Represents this object.
        :param accounts: (List[Tuple[Integer, String, String]]) -
            Represents all saved accounts for the user.
        :param default_account: (DefaultAccount[Optional]) -
            Represents the user\'s current default account.
        :param owner_id: (Integer) -
            Represents the Discord user ID who owns the accounts.

        :return: (View) -
            A view containing a select menu for switching default accounts.
        '''

        view = View(timeout=None)
        default_id = default_account.account_id if default_account else None

        if accounts:
            options = [
                disnake.SelectOption(
                    label=(
                        f'{acc[1]}'
                        if acc[2] == 'Normal'
                        else f'{acc[1]} ({acc[2]})'
                    ),
                    emoji=(
                        disnake.PartialEmoji.from_str(ACCOUNT_EMOTES.get(acc[2]))
                        if ACCOUNT_EMOTES.get(acc[2])
                        else None
                    ),
                    value=str(acc[0]),
                    default=(acc[0] == default_id)
                )
                for acc in accounts[:25]
            ]
            select = disnake.ui.Select(
                placeholder='Select a default account...',
                options=options,
                custom_id=f'acct_manager:select,{owner_id}'
            )
        else:
            select = disnake.ui.Select(
                placeholder="You don't have any accounts.",
                options=[disnake.SelectOption(label="You don't have any accounts", value='none')],
                custom_id=f'acct_manager:select,{owner_id}',
                disabled=True
            )

        view.add_item(select)

        view.add_item(
            disnake.ui.Button(
                label='⟳',
                style=disnake.ButtonStyle.secondary,
                custom_id=f'acct_manager:refresh,{owner_id}',
                row=1
            )
        )

        view.add_item(
            disnake.ui.Button(
                label='Delete',
                style=disnake.ButtonStyle.secondary,
                custom_id=f'acct_manager:delete,{owner_id},{default_id or 0}',
                row=1,
                disabled=(default_id is None)
            )
        )

        return view


    async def _send_account_manager(
        self,
        inter: MessageInteraction,
        user_id: int,
        default_account=None,
        accounts=None,
    ) -> None:
        '''
        Fetches account data for the given user and sends an ephemeral
        Account Manager response to the interaction.

        :param self: -
            Represents this object.
        :param inter: (MessageInteraction) -
            Represents the interaction that triggered the Account Manager.
        :param user_id: (Integer) -
            Represents the Discord user ID of the command author.
        :param default_account: (DefaultAccount[Optional]) -
            Represents the current default account.
        :param accounts: (List[Tuple[int, str, str]][Optional]) -
            Represents the user's saved accounts.
        :return: (None)
        '''

        if default_account is None:
            default_account = await get_default_account(self, user_id)
        if accounts is None:
            accounts = await get_user_accounts(self, user_id)
        embed = EmbedFactory().create_account_manager(
            default_account,
            accounts,
            ACCOUNT_EMOTES,
            inter.created_at
        )
        view = self._build_account_manager_view(accounts, default_account, user_id)
        await inter.response.send_message(embed=embed, view=view, ephemeral=True)


    async def search_hiscores(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        hiscore_category: str,
        account_type: str,
        username: str = None,
        owner_id: int = None,
        trace_id: str | None = None,
        operation: str = 'lookup',
        default_account=None,
        default_account_checked: bool = False,
        started_at: float | None = None,
        emit_expected_failure: bool = True,
    ) -> Tuple[disnake.Embed, disnake.ui.View, str, str, str]:
        '''
        Function which takes a username and returns hiscore
        values from the official API in a structured format.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction | MessageInteraction) -
            Represents an interaction with an application command or component.
        :param hiscore_category: (String) -
            Represents the Hiscore category (Ex: Bosses, Skills etc.)
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)
        :param username: (String[Optional]) -
            Represents a player's username.
        :param owner_id: (Integer[Optional]) -
            Represents the user ID who initiated the command.

        :return: Tuple[disnake.Embed, disnake.ui.View, str, str, str] -
            An embed and view containing the hiscore information, the
            resolved username, resolved account type, and resolution source.
        '''

        input_username = username
        working_username = username
        resolved_username = username
        resolved_account_type = account_type
        resolution_source = 'provided_username'
        default_account_id = None

        try:
            request_user = getattr(inter, 'author', None) or getattr(inter, 'user', None)
            request_user_id = owner_id or getattr(request_user, 'id', None)

            if not working_username:
                resolution_source = 'default_account'
                if not default_account_checked:
                    default_account = await get_default_account(self, request_user_id)
                if not default_account:
                    raise exceptions.UsernameNonexistent()
                default_account_id = default_account.account_id
                working_username = default_account.username
                default_account_type = default_account.account_type
                if account_type is None:
                    account_type = default_account_type
            else:
                if is_discord_mention(working_username):
                    resolution_source = 'discord_mention_lookup'
                    working_username, account_type = await get_username(
                        self, get_discord_mention_id(working_username)
                    )
                    if not working_username:
                        raise exceptions.MentionedUserAccountNonexistent()
            
            if is_invalid_username(working_username, MAX_CHARS, BLACKLIST_CHARS):
                raise exceptions.UsernameInvalid

            if not account_type:
                account_type = 'Normal'

            if owner_id is None:
                owner_id = request_user_id
            
            params = build_stats_resolution_params(
                original_username=input_username,
                resolved_username=working_username,
                resolution_source=resolution_source,
                default_account_id=default_account_id,
                account_type=account_type,
            )

            resolved_username = working_username
            resolved_account_type = account_type
            primary_param = params[0] if params else None

            self._stats_log.info(
                inter,
                build_log_message(
                    command='stats',
                    stage='resolve',
                    subject=primary_param.label if primary_param else None,
                    resolved=resolved_username,
                ),
                invocation_source=self._invocation_source(inter),
                action='resolve',
                stage='resolve',
                operation=operation,
                trace_id=trace_id,
                hiscore_category=hiscore_category,
                account_type=account_type,
                username=input_username,
                resolved_username=resolved_username,
                resolved_account_type=resolved_account_type,
                resolution_source=resolution_source,
                log_params=serialize_params(params),
                owner_id=owner_id,
            )

            if account_type == 'Normal':
                try:
                    hiscore_data = await asyncio.to_thread(
                        parse_hiscores,
                        HISCORE_API_URLS.get(account_type),
                        HEADERS,
                        HISCORES_ORDER,
                        [working_username],
                        trace_id=trace_id,
                    )
                except IndexError as exc:
                    raise exceptions.NoHiscoreData from exc

            else:
                try:
                    hiscore_data = await asyncio.to_thread(
                        parse_hiscores,
                        HISCORE_API_URLS.get(account_type),
                        HEADERS,
                        HISCORES_ORDER,
                        [working_username],
                        trace_id=trace_id,
                    )
                except (IndexError, exceptions.NoHiscoreData) as exc1:
                    try:
                        hiscore_data = await asyncio.to_thread(
                            parse_hiscores,
                            NORMAL_API,
                            HEADERS,
                            HISCORES_ORDER,
                            [working_username],
                            trace_id=trace_id,
                        )
                    except (IndexError, exceptions.NoHiscoreData) as exc2:
                        raise exceptions.NoHiscoreData from exc2
                    raise exceptions.NoGameModeData from exc1

            emote = ACCOUNT_EMOTES.get(account_type, '')
            embed = EmbedFactory().create(
                title='Personal Hiscores',
                description=(
                    f'Personal Hiscores for {emote} **{working_username}**\n\u200b\n'
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
                    working_username,
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
                    working_username,
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
                    working_username,
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
                    working_username,
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
            return embed, view, resolved_username, resolved_account_type, resolution_source

        except (
            exceptions.UsernameNonexistent,
            exceptions.MentionedUserAccountNonexistent,
            exceptions.UsernameInvalid,
            exceptions.NoHiscoreData,
            exceptions.NoGameModeData,
        ) as exc:
            fail_params = build_stats_failure_params(
                original_username=input_username,
                resolved_username=resolved_username,
                resolution_source=resolution_source,
                default_account_id=default_account_id,
                account_type=account_type,
            )
            if emit_expected_failure:
                self._stats_log.warning(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='failure',
                        operation=operation,
                    ),
                    invocation_source=self._invocation_source(inter),
                    action='fail',
                    stage='failure',
                    operation=operation,
                    trace_id=trace_id,
                    hiscore_category=hiscore_category,
                    account_type=account_type,
                    username=input_username,
                    resolved_username=resolved_username,
                    resolved_account_type=resolved_account_type,
                    resolution_source=resolution_source,
                    handled=True,
                    expected_failure=True,
                    user_visible=True,
                    exception_type=type(exc).__name__,
                    exception=str(exc),
                    log_params=serialize_params(fail_params),
                    owner_id=owner_id,
                    **({'duration_ms': elapsed_ms(started_at)} if started_at is not None else {}),
                )
            raise


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
        resolved_account_type = account_type
        trace_id = uuid.uuid4().hex

        params = []
        if username is not None:
            if is_discord_mention(username):
                params.append(
                    LogParam(
                        kind='discord_user',
                        label='discord-user',
                        value=username,
                    )
                )
            else:
                params.append(
                    LogParam(
                        kind='username',
                        label='username',
                        value=username,
                    )
                )
        primary_param = params[0] if params else None
        started_at = time.perf_counter()

        self._stats_log.info(
            inter,
            build_log_message(
                command='stats',
                stage='start',
                operation='lookup',
                subject=primary_param.label if primary_param else None,
            ),
            invocation_source=self._invocation_source(inter),
            action='start',
            stage='start',
            operation='lookup',
            trace_id=trace_id,
            hiscore_category=hiscore_category,
            account_type=account_type,
            username=username,
            log_params=serialize_params(params),
        )

        try:
            default_account = None
            default_account_checked = False
            defer_ephemeral = False
            if not username:
                default_account = await get_default_account(self, inter.author.id)
                default_account_checked = True
                defer_ephemeral = default_account is None
            elif is_invalid_username(username, MAX_CHARS, BLACKLIST_CHARS):
                defer_ephemeral = True

            await inter.response.defer(ephemeral=defer_ephemeral)
            embed, view, resolved_username, resolved_account_type, resolution_source = await self.search_hiscores(
                inter,
                hiscore_category,
                account_type,
                username,
                inter.author.id,
                trace_id=trace_id,
                default_account=default_account,
                default_account_checked=default_account_checked,
                started_at=started_at,
            )
            await inter.followup.send(
                embed=embed,
                view=view
            )

            self._stats_log.success(
                inter,
                build_log_message(
                    command='stats',
                    stage='complete',
                    operation='lookup',
                ),
                invocation_source=self._invocation_source(inter),
                action='complete',
                stage='complete',
                operation='lookup',
                trace_id=trace_id,
                hiscore_category=hiscore_category,
                account_type=account_type,
                resolved_account_type=resolved_account_type,
                username=username,
                resolved_username=resolved_username,
                resolution_source=resolution_source,
                log_params=serialize_resolved_username(
                    resolved_username,
                    account_type=resolved_account_type,
                    resolution_source=resolution_source
                ),
                duration_ms=elapsed_ms(started_at),
            )

        except (
            exceptions.UsernameNonexistent,
            exceptions.MentionedUserAccountNonexistent,
            exceptions.UsernameInvalid,
            exceptions.NoHiscoreData,
            exceptions.NoGameModeData,
        ) as exc:
            is_ephemeral_failure = isinstance(exc, (
                exceptions.UsernameNonexistent,
                exceptions.MentionedUserAccountNonexistent,
                exceptions.UsernameInvalid,
            ))

            if isinstance(exc, (
                exceptions.NoHiscoreData,
                exceptions.UsernameInvalid,
            )):
                colour = 0xB72615
            else:
                colour = 0x8B8B8B

            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=str(exc),
                thumbnail_url=None,
                colour=colour,
                button_label='Support Server',
                button_url=SUPPORT_SERVER
            )
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
            if inter.response.is_done():
                await inter.followup.send(
                    embed=embed,
                    view=view,
                    ephemeral=is_ephemeral_failure
                )
            else:
                await inter.response.send_message(
                    embed=embed,
                    view=view,
                    ephemeral=is_ephemeral_failure
                )
            return

        except Exception as exc:
            self._stats_log.error(
                inter,
                build_log_message(
                    command='stats',
                    stage='runtime_failure',
                    operation='lookup',
                ),
                exc=exc,
                invocation_source=self._invocation_source(inter),
                action='fail',
                stage='runtime_failure',
                operation='lookup',
                trace_id=trace_id,
                hiscore_category=hiscore_category,
                account_type=account_type,
                resolved_account_type=resolved_account_type,
                username=username,
                handled=True,
                expected_failure=False,
                user_visible=True,
                duration_ms=elapsed_ms(started_at),
            )
            await ack_runtime_failure(inter)
            return


    @commands.Cog.listener('on_button_click')
    async def button_listener(
        self,
        inter: MessageInteraction
    ) -> None:
        '''
        Cog listener which handles button clicks for /stats navigation and refresh.

        :param self: -
            Represents this object.
        :param inter: (MessageInteraction) -
            Represents a message component interaction triggered by a stats button.

        :return: (None)
        '''
        custom_id = inter.component.custom_id

        if not custom_id:
            return

        if not custom_id.startswith(('acct_del:', 'acct_manager:', 'stats:')):
            return

        trace_id = uuid.uuid4().hex
        raw_payload = custom_id.split(':', 1)[1]
        raw_params = raw_payload.split(',')
        raw_action = raw_params[0] if raw_params else None
        component_prefix = custom_id.split(':', 1)[0]
        operation = {
            ('acct_del', 'no', 5): 'account_delete_cancel',
            ('acct_del', 'ok', 5): 'account_delete_confirm',
            ('acct_manager', 'refresh', 2): 'account_manager_refresh',
            ('acct_manager', 'delete', 3): 'account_delete',
            ('stats', 'account_manager', 2): 'account_manager',
            ('stats', 'navigate', 5): 'navigate',
            ('stats', 'refresh', 5): 'refresh',
        }.get(
            (component_prefix, raw_action, len(raw_params)),
            'invalid_component',
        )
        origin_candidate = raw_params[4] if len(raw_params) == 5 else None
        origin_trace_id = (
            origin_candidate
            if (
                component_prefix == 'acct_del'
                and raw_action in ('no', 'ok')
                and isinstance(origin_candidate, str)
                and len(origin_candidate) == 32
                and all(char in '0123456789abcdefABCDEF' for char in origin_candidate)
            )
            else None
        )
        started_at = time.perf_counter()
        self._log_component_start(
            inter,
            trace_id,
            operation,
            component_type='button',
            origin_trace_id=origin_trace_id,
        )

        if custom_id.startswith('acct_del:'):
            payload = custom_id.removeprefix('acct_del:')
            params = payload.split(',')

            if len(params) != 5:
                await self._ack_invalid_stats_component(inter, trace_id, started_at)
                return

            action, owner_id, account_id, manager_message_id, _raw_origin_trace_id = params

            if str(inter.author.id) != owner_id:
                await ack_wrong_component_user(
                    inter,
                    self._stats_log,
                    'stats',
                    invocation_source=self._invocation_source(inter),
                    trace_id=trace_id,
                    origin_trace_id=origin_trace_id,
                    started_at=started_at,
                )
                return

            if action == 'no':
                try:
                    await inter.response.defer()
                    await inter.delete_original_response()
                    self._stats_log.success(
                        inter,
                        build_log_message(
                            command='stats',
                            stage='complete',
                            operation='account_delete_cancel',
                        ),
                        trace_id=trace_id,
                        origin_trace_id=origin_trace_id,
                        invocation_source=self._invocation_source(inter),
                        action='complete',
                        stage='complete',
                        operation='account_delete_cancel',
                        owner_id=owner_id,
                        component_type='button',
                        account_id=account_id,
                        duration_ms=elapsed_ms(started_at),
                    )
                except Exception as exc:
                    self._stats_log.error(
                        inter,
                        build_log_message(
                            command='stats',
                            stage='runtime_failure',
                            operation='account_delete_cancel',
                        ),
                        exc=exc,
                        trace_id=trace_id,
                        origin_trace_id=origin_trace_id,
                        invocation_source=self._invocation_source(inter),
                        action='fail',
                        stage='runtime_failure',
                        operation='account_delete_cancel',
                        owner_id=owner_id,
                        component_type='button',
                        account_id=account_id,
                        handled=False,
                        expected_failure=False,
                        user_visible=False,
                        duration_ms=elapsed_ms(started_at),
                    )
                    raise
                return

            if action != 'ok':
                await self._ack_invalid_stats_component(inter, trace_id, started_at)
                return

            try:
                await inter.response.defer()
                deleted = await remove_user_account(
                    self,
                    int(owner_id),
                    int(account_id)
                )

                await inter.delete_original_response()

                if deleted:
                    default_account = await get_default_account(self, int(owner_id))
                    accounts = await get_user_accounts(self, int(owner_id))
                    embed = EmbedFactory().create_account_manager(
                        default_account,
                        accounts,
                        ACCOUNT_EMOTES,
                        inter.created_at
                    )
                    view = self._build_account_manager_view(
                        accounts,
                        default_account,
                        int(owner_id)
                    )

                    try:
                        await inter.followup.edit_message(
                            int(manager_message_id),
                            embed=embed,
                            view=view
                        )
                    except Exception:
                        await inter.followup.send(
                            embed=embed,
                            view=view,
                            ephemeral=True
                        )

                self._stats_log.success(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='complete',
                        operation='account_delete_confirm',
                    ),
                    trace_id=trace_id,
                    origin_trace_id=origin_trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='complete',
                    stage='complete',
                    operation='account_delete_confirm',
                    owner_id=owner_id,
                    component_type='button',
                    account_id=account_id,
                    deleted=deleted,
                    duration_ms=elapsed_ms(started_at),
                )
            except Exception as exc:
                self._stats_log.error(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='runtime_failure',
                        operation='account_delete_confirm',
                    ),
                    exc=exc,
                    trace_id=trace_id,
                    origin_trace_id=origin_trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='fail',
                    stage='runtime_failure',
                    operation='account_delete_confirm',
                    owner_id=owner_id,
                    component_type='button',
                    account_id=account_id,
                    handled=True,
                    expected_failure=False,
                    user_visible=True,
                    duration_ms=elapsed_ms(started_at),
                )
                raise
            return

        if custom_id.startswith('acct_manager:'):
            payload = custom_id.removeprefix('acct_manager:')
            params = payload.split(',')

            if not params:
                await self._ack_invalid_stats_component(inter, trace_id, started_at)
                return

            action = params[0]

            if action == 'refresh':
                if len(params) != 2:
                    await self._ack_invalid_stats_component(inter, trace_id, started_at)
                    return

                _, owner_id = params
                if str(inter.author.id) != owner_id:
                    await ack_wrong_component_user(
                        inter,
                        self._stats_log,
                        'stats',
                        invocation_source=self._invocation_source(inter),
                        trace_id=trace_id,
                        started_at=started_at,
                    )
                    return

                default_account = None
                accounts = None
                try:
                    default_account = await get_default_account(self, int(owner_id))
                    accounts = await get_user_accounts(self, int(owner_id))

                    loading_view = build_loading_button_view(inter)
                    await inter.response.edit_message(view=loading_view)

                    embed = EmbedFactory().create_account_manager(
                        default_account,
                        accounts,
                        ACCOUNT_EMOTES,
                        inter.created_at
                    )
                    view = self._build_account_manager_view(
                        accounts,
                        default_account,
                        int(owner_id)
                    )
                    await inter.edit_original_response(embed=embed, view=view)

                    self._stats_log.success(
                        inter,
                        build_log_message(
                            command='stats',
                            stage='complete',
                            operation='account_manager_refresh',
                        ),
                        trace_id=trace_id,
                        invocation_source=self._invocation_source(inter),
                        action='complete',
                        stage='complete',
                        operation='account_manager_refresh',
                        owner_id=owner_id,
                        component_type='button',
                        accounts_count=len(accounts),
                        has_default_account=bool(default_account),
                        default_account_id=getattr(default_account, 'account_id', None),
                        default_username=getattr(default_account, 'username', None),
                        default_account_type=getattr(default_account, 'account_type', None),
                        duration_ms=elapsed_ms(started_at),
                    )

                except Exception as exc:
                    self._stats_log.error(
                        inter,
                        build_log_message(
                            command='stats',
                            stage='runtime_failure',
                            operation='account_manager_refresh',
                        ),
                        exc=exc,
                        trace_id=trace_id,
                        invocation_source=self._invocation_source(inter),
                        action='fail',
                        stage='runtime_failure',
                        operation='account_manager_refresh',
                        owner_id=owner_id,
                        component_type='button',
                        accounts_count=len(accounts) if accounts is not None else None,
                        has_default_account=(
                            bool(default_account)
                            if default_account is not None or accounts is not None
                            else None
                        ),
                        default_account_id=getattr(default_account, 'account_id', None),
                        default_username=getattr(default_account, 'username', None),
                        default_account_type=getattr(default_account, 'account_type', None),
                        handled=True,
                        expected_failure=False,
                        user_visible=True,
                        duration_ms=elapsed_ms(started_at),
                    )
                    raise
                return

            if action == 'delete':
                if len(params) != 3:
                    await self._ack_invalid_stats_component(inter, trace_id, started_at)
                    return

                _, owner_id, account_id = params
                manager_message_id = str(inter.message.id)

                if str(inter.author.id) != owner_id:
                    await ack_wrong_component_user(
                        inter,
                        self._stats_log,
                        'stats',
                        invocation_source=self._invocation_source(inter),
                        trace_id=trace_id,
                        started_at=started_at,
                    )
                    return

                if account_id == '0':
                    await ack_component_failure(
                        inter,
                        self._stats_log,
                        'stats',
                        description='You do not have a default account to delete.',
                        operation='account_delete_no_default',
                        invocation_source=self._invocation_source(inter),
                        trace_id=trace_id,
                        started_at=started_at,
                    )
                    return

                try:
                    owner_accounts = await get_user_accounts(self, int(owner_id))
                    target_account = next(
                        (acc for acc in owner_accounts if str(acc[0]) == account_id),
                        None
                    )
                    account_name = target_account[1] if target_account else 'selected account'

                    confirm_embed = EmbedFactory().create(
                        title='Confirmation',
                        description=(
                            f'Are you sure you want to delete the account **{account_name}**? '
                            'You can re-add the account with </setrsn:1114968268864753754> at any time.'
                        ),
                        colour=0xB72615
                    )
                    confirm_embed.timestamp = inter.created_at
                    confirm_embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

                    confirm_view = View(timeout=None)
                    confirm_view.add_item(
                        disnake.ui.Button(
                            label='Confirm',
                            style=disnake.ButtonStyle.danger,
                            custom_id=(
                                f'acct_del:ok,{owner_id},{account_id},'
                                f'{manager_message_id},{trace_id}'
                            )
                        )
                    )
                    confirm_view.add_item(
                        disnake.ui.Button(
                            label='Cancel',
                            style=disnake.ButtonStyle.secondary,
                            custom_id=(
                                f'acct_del:no,{owner_id},{account_id},'
                                f'{manager_message_id},{trace_id}'
                            )
                        )
                    )

                    await inter.response.send_message(
                        embed=confirm_embed,
                        view=confirm_view,
                        ephemeral=True
                    )
                    self._stats_log.success(
                        inter,
                        build_log_message(
                            command='stats',
                            stage='complete',
                            operation='account_delete',
                        ),
                        trace_id=trace_id,
                        invocation_source=self._invocation_source(inter),
                        action='complete',
                        stage='complete',
                        operation='account_delete',
                        owner_id=owner_id,
                        component_type='button',
                        account_id=account_id,
                        duration_ms=elapsed_ms(started_at),
                    )
                except Exception as exc:
                    self._stats_log.error(
                        inter,
                        build_log_message(
                            command='stats',
                            stage='runtime_failure',
                            operation='account_delete',
                        ),
                        exc=exc,
                        trace_id=trace_id,
                        invocation_source=self._invocation_source(inter),
                        action='fail',
                        stage='runtime_failure',
                        operation='account_delete',
                        owner_id=owner_id,
                        component_type='button',
                        account_id=account_id,
                        handled=True,
                        expected_failure=False,
                        user_visible=True,
                        duration_ms=elapsed_ms(started_at),
                    )
                    raise
                return

            await self._ack_invalid_stats_component(inter, trace_id, started_at)
            return

        if not custom_id.startswith('stats:'):
            return

        payload = custom_id.removeprefix('stats:')
        params = payload.split(',')

        if not params:
            await self._ack_invalid_stats_component(inter, trace_id, started_at)
            return

        action = params[0]

        if action == 'account_manager':
            if len(params) != 2:
                await self._ack_invalid_stats_component(inter, trace_id, started_at)
                return
            owner_id = params[1]
            if str(inter.author.id) != owner_id:
                await ack_wrong_component_user(
                    inter,
                    self._stats_log,
                    'stats',
                    invocation_source=self._invocation_source(inter),
                    trace_id=trace_id,
                    started_at=started_at,
                )
                return

            default_account = None
            accounts = None
            try:
                default_account = await get_default_account(self, int(owner_id))
                accounts = await get_user_accounts(self, int(owner_id))

                await self._send_account_manager(
                    inter,
                    int(owner_id),
                    default_account=default_account,
                    accounts=accounts,
                )
                self._stats_log.success(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='complete',
                        operation='account_manager',
                    ),
                    trace_id=trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='complete',
                    stage='complete',
                    operation='account_manager',
                    owner_id=owner_id,
                    component_type='button',
                    accounts_count=len(accounts),
                    has_default_account=bool(default_account),
                    default_account_id=getattr(default_account, 'account_id', None),
                    default_username=getattr(default_account, 'username', None),
                    default_account_type=getattr(default_account, 'account_type', None),
                    duration_ms=elapsed_ms(started_at),
                )
            except Exception as exc:
                self._stats_log.error(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='runtime_failure',
                        operation='account_manager',
                    ),
                    exc=exc,
                    trace_id=trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='fail',
                    stage='runtime_failure',
                    operation='account_manager',
                    owner_id=owner_id,
                    component_type='button',
                    accounts_count=len(accounts) if accounts is not None else None,
                    has_default_account=(
                        bool(default_account)
                        if default_account is not None or accounts is not None
                        else None
                    ),
                    default_account_id=getattr(default_account, 'account_id', None),
                    default_username=getattr(default_account, 'username', None),
                    default_account_type=getattr(default_account, 'account_type', None),
                    handled=True,
                    expected_failure=False,
                    user_visible=True,
                    duration_ms=elapsed_ms(started_at),
                )
                raise
            return

        if action not in ['navigate', 'refresh']:
            await self._ack_invalid_stats_component(inter, trace_id, started_at)
            return

        if len(params) != 5:
            await self._ack_invalid_stats_component(inter, trace_id, started_at)
            return

        _, hiscore_category, account_type, resolved_username, owner_id = params

        if str(inter.author.id) != owner_id:
            await ack_wrong_component_user(
                inter,
                self._stats_log,
                'stats',
                invocation_source=self._invocation_source(inter),
                trace_id=trace_id,
                started_at=started_at,
            )
            return

        resolved_account_type = None
        try:
            loading_view = build_loading_button_view(inter)
            await inter.response.edit_message(view=loading_view)

            embed, view, resolved_username, resolved_account_type, _ = await self.search_hiscores(
                inter,
                hiscore_category,
                account_type,
                resolved_username,
                int(owner_id),
                trace_id=trace_id,
                operation=action,
                started_at=started_at,
                emit_expected_failure=False,
            )
            await inter.edit_original_response(
                embed=embed,
                view=view
            )

            if action == 'navigate':
                self._stats_log.success(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='complete',
                        operation='navigate',
                    ),
                    trace_id=trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='complete',
                    stage='complete',
                    operation='navigate',
                    hiscore_category=hiscore_category,
                    account_type=resolved_account_type,
                    resolved_username=resolved_username,
                    resolved_account_type=resolved_account_type,
                    owner_id=owner_id,
                    component_type='button',
                    log_params=serialize_resolved_username(
                        resolved_username,
                        account_type=resolved_account_type,
                        resolution_source='button_navigate',
                    ),
                    duration_ms=elapsed_ms(started_at),
                )
            else:
                self._stats_log.success(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='complete',
                        operation='refresh',
                    ),
                    trace_id=trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='complete',
                    stage='complete',
                    operation='refresh',
                    hiscore_category=hiscore_category,
                    account_type=resolved_account_type,
                    resolved_username=resolved_username,
                    resolved_account_type=resolved_account_type,
                    owner_id=owner_id,
                    component_type='button',
                    log_params=serialize_resolved_username(
                        resolved_username,
                        account_type=resolved_account_type,
                        resolution_source='button_refresh',
                    ),
                    duration_ms=elapsed_ms(started_at),
                )

        except (
            exceptions.UsernameNonexistent,
            exceptions.MentionedUserAccountNonexistent,
            exceptions.UsernameInvalid,
            exceptions.NoHiscoreData,
            exceptions.NoGameModeData,
        ) as exc:
            try:
                view = self._build_stats_view(
                    hiscore_category,
                    account_type,
                    resolved_username,
                    int(owner_id)
                )
                if isinstance(exc, (
                    exceptions.NoHiscoreData,
                    exceptions.UsernameInvalid,
                )):
                    colour = 0xB72615
                else:
                    colour = 0x8B8B8B

                embed, _ = EmbedFactory().create(
                    title='Nothing interesting happens.',
                    description=str(exc),
                    thumbnail_url=None,
                    colour=colour,
                    button_label='Support Server',
                    button_url=SUPPORT_SERVER
                )
                embed.timestamp = inter.created_at
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
                await inter.edit_original_response(embed=embed, view=view)
            except Exception as fallback_exc:
                self._stats_log.error(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='runtime_failure',
                        operation=action,
                    ),
                    exc=exc,
                    trace_id=trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='fail',
                    stage='runtime_failure',
                    operation=action,
                    component_type='button',
                    handled=False,
                    expected_failure=False,
                    user_visible=False,
                    fallback_exception_type=type(fallback_exc).__name__,
                    fallback_exception=str(fallback_exc),
                    duration_ms=elapsed_ms(started_at),
                )
                raise exc from fallback_exc

            self._stats_log.warning(
                inter,
                build_log_message(
                    command='stats',
                    stage='failure',
                    operation=action,
                ),
                trace_id=trace_id,
                invocation_source=self._invocation_source(inter),
                action='fail',
                stage='failure',
                operation=action,
                hiscore_category=hiscore_category,
                account_type=account_type,
                resolved_username=resolved_username,
                owner_id=owner_id,
                component_type='button',
                handled=True,
                expected_failure=True,
                user_visible=True,
                exception_type=type(exc).__name__,
                exception=str(exc),
                duration_ms=elapsed_ms(started_at),
            )
            return

        except Exception as exc:
            view = self._build_stats_view(
                hiscore_category,
                account_type,
                resolved_username,
                int(owner_id)
            )
            await inter.edit_original_response(view=view)
            self._stats_log.error(
                inter,
                build_log_message(
                    command='stats',
                    stage='runtime_failure',
                    operation=action,
                ),
                exc=exc,
                trace_id=trace_id,
                invocation_source=self._invocation_source(inter),
                action='fail',
                stage='runtime_failure',
                operation=action,
                hiscore_category=hiscore_category,
                account_type=resolved_account_type,
                resolved_username=resolved_username,
                resolved_account_type=resolved_account_type,
                owner_id=owner_id,
                component_type='button',
                handled=True,
                expected_failure=False,
                user_visible=True,
                duration_ms=elapsed_ms(started_at),
            )
            raise


    @commands.Cog.listener('on_dropdown')
    async def dropdown_listener(
        self,
        inter: MessageInteraction
    ) -> None:
        '''
        Cog listener which handles dropdown selections for the Account Manager.

        :param self: -
            Represents this object.
        :param inter: (MessageInteraction) -
            Represents a message component interaction triggered by the
            Account Manager select menu.

        :return: (None)
        '''

        custom_id = inter.component.custom_id

        if not custom_id or not custom_id.startswith('acct_manager:'):
            return

        trace_id = uuid.uuid4().hex
        started_at = time.perf_counter()
        self._log_component_start(
            inter,
            trace_id,
            'default_account_select',
            component_type='dropdown',
        )

        payload = custom_id.removeprefix('acct_manager:')
        params = payload.split(',')

        if len(params) != 2:
            await self._ack_invalid_stats_component(inter, trace_id, started_at)
            return

        action, owner_id = params

        if action != 'select':
            await self._ack_invalid_stats_component(inter, trace_id, started_at)
            return

        if str(inter.author.id) != owner_id:
            await ack_wrong_component_user(
                inter,
                self._stats_log,
                'stats',
                invocation_source=self._invocation_source(inter),
                trace_id=trace_id,
                started_at=started_at,
            )
            return

        selected_value = inter.values[0] if inter.values else None
        if selected_value is None:
            await self._ack_invalid_stats_component(inter, trace_id, started_at)
            return
        if selected_value == 'none':
            try:
                await inter.response.defer()
            except Exception as exc:
                self._stats_log.error(
                    inter,
                    build_log_message(
                        command='stats',
                        stage='runtime_failure',
                        operation='default_account_select',
                    ),
                    exc=exc,
                    trace_id=trace_id,
                    invocation_source=self._invocation_source(inter),
                    action='fail',
                    stage='runtime_failure',
                    operation='default_account_select',
                    component_type='dropdown',
                    owner_id=owner_id,
                    selected_value=selected_value,
                    handled=False,
                    expected_failure=False,
                    user_visible=False,
                    duration_ms=elapsed_ms(started_at),
                )
                raise

            self._stats_log.warning(
                inter,
                build_log_message(
                    command='stats',
                    stage='failure',
                    operation='default_account_select',
                ),
                trace_id=trace_id,
                invocation_source=self._invocation_source(inter),
                action='fail',
                stage='failure',
                operation='default_account_select',
                component_type='dropdown',
                owner_id=owner_id,
                selected_value=selected_value,
                handled=True,
                expected_failure=True,
                user_visible=False,
                duration_ms=elapsed_ms(started_at),
            )
            return

        selected_username = None
        selected_account_type = None
        acknowledgement_failed = False
        try:
            all_accounts = await get_user_accounts(self, int(owner_id))
            selected_account = next(
                (acc for acc in all_accounts if str(acc[0]) == selected_value), None
            )
            if selected_account is None:
                try:
                    await ack_component_failure(
                        inter,
                        self._stats_log,
                        'stats',
                        description='That account is no longer available. Please refresh the account manager.',
                        operation='default_account_select',
                        invocation_source=self._invocation_source(inter),
                        trace_id=trace_id,
                        started_at=started_at,
                        emit_runtime_failure=False,
                    )
                except Exception:
                    acknowledgement_failed = True
                    raise
                return
            selected_username = selected_account[1] if selected_account else None
            selected_account_type = selected_account[2] if selected_account else None
            await inter.response.defer()

            user_id = int(owner_id)
            await set_default_account(self, user_id, int(selected_value))

            default_account = await get_default_account(self, user_id)
            accounts = await get_user_accounts(self, user_id)
            embed = EmbedFactory().create_account_manager(
                default_account,
                accounts,
                ACCOUNT_EMOTES,
                inter.created_at
            )
            view = self._build_account_manager_view(accounts, default_account, user_id)
            await inter.edit_original_response(embed=embed, view=view)

            self._stats_log.success(
                inter,
                build_log_message(
                    command='stats',
                    stage='complete',
                    operation='default_account_select',
                ),
                trace_id=trace_id,
                invocation_source=self._invocation_source(inter),
                action='complete',
                stage='complete',
                operation='default_account_select',
                owner_id=owner_id,
                component_type='dropdown',
                selected_value=selected_value,
                selected_username=selected_username,
                selected_account_type=selected_account_type,
                duration_ms=elapsed_ms(started_at),
            )

        except Exception as exc:
            self._stats_log.error(
                inter,
                build_log_message(
                    command='stats',
                    stage='runtime_failure',
                    operation='default_account_select',
                ),
                exc=exc,
                trace_id=trace_id,
                invocation_source=self._invocation_source(inter),
                action='fail',
                stage='runtime_failure',
                operation='default_account_select',
                owner_id=owner_id,
                component_type='dropdown',
                selected_value=selected_value,
                selected_username=selected_username,
                selected_account_type=selected_account_type,
                handled=not acknowledgement_failed,
                expected_failure=False,
                user_visible=not acknowledgement_failed,
                duration_ms=elapsed_ms(started_at),
            )
            raise


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
